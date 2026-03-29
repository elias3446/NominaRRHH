from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

from .models.profile_models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        exclude = ('user', 'id')  # El usuario y ID se vinculan automáticamente desde el padre
        
class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializador completo del usuario que incluye su perfil en el esquema público.
    """
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'role', 'is_super_admin', 'created_at', 'updated_at', 'last_login', 
            'email_confirmed_at', 'phone', 'phone_confirmed_at', 
            'banned_until', 'is_sso_user', 'raw_app_meta_data', 'raw_user_meta_data',
            'profile'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'last_login', 'email_confirmed_at', 'phone_confirmed_at')
        
class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de nuevos usuarios en Swissport/NominaRRHH.
    Crea el usuario y un perfil inicial vacío.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'profile')

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        else:
            # Crea un perfil vacío por defecto si no se especifican datos iniciales
            UserProfile.objects.create(user=user, first_name='', last_name='')
        return user

class DepartmentSerializer(serializers.ModelSerializer):
    """
    Serializador robusto para la entrada de datos de Departamentos.
    Permite creación opcional de cargos asíncronamente a través del campo job_roles.
    """
    created_by_info = UserDetailSerializer(source='created_by', read_only=True)
    updated_by_info = UserDetailSerializer(source='updated_by', read_only=True)
    
    # Campo para recibir cargos a crear junto con el departamento
    job_roles = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        from .models.department_models import Department  # Import dinámico para evitar circularidad
        model = Department
        fields = (
            'id', 'name', 'description', 
            'created_at', 'updated_at', 
            'created_by', 'updated_by',
            'created_by_info', 'updated_by_info',
            'job_roles'
        )
        read_only_fields = (
            'id', 'created_at', 'updated_at', 
            'created_by', 'updated_by',
            'created_by_info', 'updated_by_info'
        )

    def validate_name(self, value):
        from .models.department_models import Department
        value_norm = value.strip().upper()
        qs = Department.objects.filter(name__iexact=value_norm, deleted_at__isnull=True)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
            
        if qs.exists():
            raise serializers.ValidationError("Ya existe un departamento con este nombre.")
        return value

    def create(self, validated_data):
        from .models.job_role_models import JobRole
        
        job_roles_data = validated_data.pop('job_roles', [])
        department = super().create(validated_data)
        
        created_roles = []
        for role_data in job_roles_data:
            role_name = role_data.get('name', '').strip()
            if not role_name:
                continue
                
            job_role = JobRole.objects.create(
                department=department,
                name=role_name,
                description=role_data.get('description', ''),
                created_by=validated_data.get('created_by'),
                updated_by=validated_data.get('updated_by')
            )
            created_roles.append(job_role)
            
        # Adjuntamos como atributo temporal para poder emitir eventos en WS
        department._created_roles = created_roles
        return department

class JobRoleSerializer(serializers.ModelSerializer):
    """
    Serializador robusto para Cargos.
    Incluye información de trazabilidad y del departamento asociado.
    """
    created_by_info = UserDetailSerializer(source='created_by', read_only=True)
    updated_by_info = UserDetailSerializer(source='updated_by', read_only=True)
    department_info = DepartmentSerializer(source='department', read_only=True)

    class Meta:
        from .models.job_role_models import JobRole
        model = JobRole
        fields = (
            'id', 'name', 'description', 'department', 
            'created_at', 'updated_at', 
            'created_by', 'updated_by',
            'created_by_info', 'updated_by_info', 'department_info'
        )
        read_only_fields = (
            'id', 'created_at', 'updated_at', 
            'created_by', 'updated_by',
            'created_by_info', 'updated_by_info', 'department_info'
        )

    def validate_name(self, value):
        from .models.job_role_models import JobRole
        # Validar que no exista un cargo con el mismo nombre EN EL MISMO DEPARTAMENTO
        # (solo si no está borrado lógicamente)
        dept_id = self.initial_data.get('department')
        if not dept_id and self.instance:
            dept_id = self.instance.department.id

        if dept_id:
            qs = JobRole.objects.filter(
                name__iexact=value.strip(), 
                department_id=dept_id,
                deleted_at__isnull=True
            )
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise serializers.ValidationError("Este cargo ya existe en el departamento seleccionado.")
        
        return value.strip()
