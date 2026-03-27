import asyncio
import websockets
import json

async def test_auth_cycle():
    uri = "ws://localhost:8000/ws/auth/"
    async with websockets.connect(uri) as websocket:
        print(f"Conectado a {uri}")
        
        # 1. LOGIN
        payload_login = {
            "type": "login",
            "email": "test_definitivo@example.com",
            "password": "pass123"
        }
        
        print(f"\n[LOGIN] Enviando para: {payload_login['email']}")
        await websocket.send(json.dumps(payload_login))
        
        response = await websocket.recv()
        data = json.loads(response)
        
        print(f"[LOGIN] Respuesta: {data.get('status')} - {data.get('message')}")
        
        if data.get('status') == 'success':
            refresh_token = data['auth_data']['refresh']
            print(f"Refresh Token obtenido: {refresh_token[:20]}...")
            
            # 2. LOGOUT
            payload_logout = {
                "type": "logout",
                "refresh": refresh_token
            }
            
            print("\n[LOGOUT] Enviando Refresh Token para revocación...")
            await websocket.send(json.dumps(payload_logout))
            
            logout_response = await websocket.recv()
            logout_data = json.loads(logout_response)
            
            print(f"[LOGOUT] Respuesta final: {logout_data.get('status')} - {logout_data.get('message')}")
            
            if logout_data.get('status') == 'success':
                print("\n✅ SESION CERRADA CORRECTAMENTE!")
            else:
                print("\n❌ FALLO AL CERRAR SESION")

if __name__ == "__main__":
    try:
        asyncio.run(test_auth_cycle())
    except Exception as e:
        print(f"Error de conexión: {e}")
