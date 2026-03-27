import asyncio
import websockets
import json

async def test_login():
    # Nos conectamos al puerto 8000 donde corre daphne
    uri = "ws://localhost:8000/ws/auth/"
    async with websockets.connect(uri) as websocket:
        print(f"Conectado a {uri}")
        
        # Credenciales del usuario validado para Swissport
        payload = {
            "type": "login",
            "email": "test_definitivo@example.com",
            "password": "pass123"
        }
        
        print(f"Enviando credenciales para: {payload['email']}")
        await websocket.send(json.dumps(payload))
        
        response = await websocket.recv()
        data = json.loads(response)
        
        print("\n--- RESPUESTA DE AUTENTICACION ---")
        print(json.dumps(data, indent=2))
        
        if data.get('status') == 'success':
            print("\n✅ LOGIN EXITOSO!")
            print(f"Access Token: {data['auth_data']['access'][:40]}...")
        else:
            print("\n❌ LOGIN FALLIDO: " + data.get('message', 'Error desconocido'))

if __name__ == "__main__":
    try:
        asyncio.run(test_login())
    except Exception as e:
        print(f"Error de conexión: {e}")
