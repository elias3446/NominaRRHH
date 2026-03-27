from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de nuevos usuarios en Swissport/NominaRRHH.
    Valida email único y fuerza validación de contraseña de Django.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    class Meta:
        model = User
        fields = ('email', 'password')

    def create(self, validated_data):
        # Usamos el manager personalizado para crear el usuario en el esquema de Supabase
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
