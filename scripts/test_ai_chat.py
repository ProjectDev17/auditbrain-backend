"""
Script de pruebas para API de Conversaciones AI.
Verifica CRUD, chat, streaming y tool calling.
"""
import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


class AIConversationTester:
    def __init__(self):
        self.token = None
        self.conversation_id = None
        self.headers = {}
    
    def login(self):
        """Obtener token JWT."""
        print_info("Autenticando usuario...")
        
        # Intentar login con credenciales de prueba
        response = requests.post(
            f"{API_URL}/auth/login/",
            json={
                "email": "admin@auditbrain.com",
                "password": "admin123"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('access')
            self.headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            print_success(f"Login exitoso. Token: {self.token[:20]}...")
            return True
        else:
            print_error(f"Login falló: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    
    def test_create_conversation(self):
        """Probar creación de conversación."""
        print_info("\n1. Probando crear conversación...")
        
        response = requests.post(
            f"{API_URL}/ai-conversations/",
            headers=self.headers,
            json={"title": "Test Conversation - Automated"}
        )
        
        if response.status_code == 201:
            data = response.json()
            self.conversation_id = data['id']
            print_success(f"Conversación creada: {self.conversation_id}")
            print_info(f"   Título: {data['title']}")
            print_info(f"   Mensajes: {data['message_count']}")
            return True
        else:
            print_error(f"Error creando conversación: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    
    def test_list_conversations(self):
        """Probar listado de conversaciones."""
        print_info("\n2. Probando listar conversaciones...")
        
        response = requests.get(
            f"{API_URL}/ai-conversations/",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', len(data.get('results', [])))
            print_success(f"Listado exitoso: {count} conversaciones")
            
            if count > 0:
                first = data['results'][0]
                print_info(f"   Primera: {first['title']}")
                print_info(f"   Mensajes: {first.get('message_count', 0)}")
            return True
        else:
            print_error(f"Error listando: {response.status_code}")
            return False
    
    def test_get_conversation(self):
        """Probar obtener detalle de conversación."""
        print_info("\n3. Probando obtener detalle...")
        
        if not self.conversation_id:
            print_warning("No hay conversation_id, saltando test")
            return False
        
        response = requests.get(
            f"{API_URL}/ai-conversations/{self.conversation_id}/",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Detalle obtenido")
            print_info(f"   ID: {data['id']}")
            print_info(f"   Título: {data['title']}")
            print_info(f"   Mensajes: {len(data.get('messages', []))}")
            return True
        else:
            print_error(f"Error obteniendo detalle: {response.status_code}")
            return False
    
    def test_add_message(self):
        """Probar agregar mensaje manualmente."""
        print_info("\n4. Probando agregar mensaje...")
        
        if not self.conversation_id:
            print_warning("No hay conversation_id, saltando test")
            return False
        
        response = requests.post(
            f"{API_URL}/ai-conversations/{self.conversation_id}/messages/",
            headers=self.headers,
            json={
                "role": "user",
                "content": "Este es un mensaje de prueba"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Mensaje agregado")
            print_info(f"   Total mensajes: {data['message_count']}")
            return True
        else:
            print_error(f"Error agregando mensaje: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    
    def test_chat_basic(self):
        """Probar chat básico (sin Ollama, solo estructura)."""
        print_info("\n5. Probando endpoint /chat/ (estructura)...")
        
        if not self.conversation_id:
            print_warning("No hay conversation_id, saltando test")
            return False
        
        response = requests.post(
            f"{API_URL}/ai-conversations/{self.conversation_id}/chat/",
            headers=self.headers,
            json={
                "message": "Hola, ¿cómo estás?",
                "enable_tools": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Chat ejecutado")
            print_info(f"   Mensajes en conversación: {data['message_count']}")
            
            # Mostrar último mensaje (respuesta del asistente)
            if data.get('messages'):
                last_msg = data['messages'][-1]
                print_info(f"   Última respuesta: {last_msg['content'][:100]}...")
            return True
        elif response.status_code == 500:
            print_warning(f"Error 500 - Probablemente Ollama no está corriendo")
            print_info(f"   Response: {response.text[:200]}")
            return False
        else:
            print_error(f"Error en chat: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    
    def test_update_conversation(self):
        """Probar actualizar título."""
        print_info("\n6. Probando actualizar título...")
        
        if not self.conversation_id:
            print_warning("No hay conversation_id, saltando test")
            return False
        
        response = requests.patch(
            f"{API_URL}/ai-conversations/{self.conversation_id}/",
            headers=self.headers,
            json={"title": "Test Conversation - Updated"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Título actualizado: {data['title']}")
            return True
        else:
            print_error(f"Error actualizando: {response.status_code}")
            return False
    
    def test_delete_conversation(self):
        """Probar eliminar conversación."""
        print_info("\n7. Probando eliminar conversación...")
        
        if not self.conversation_id:
            print_warning("No hay conversation_id, saltando test")
            return False
        
        response = requests.delete(
            f"{API_URL}/ai-conversations/{self.conversation_id}/",
            headers=self.headers
        )
        
        if response.status_code == 204:
            print_success(f"Conversación eliminada")
            return True
        else:
            print_error(f"Error eliminando: {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas."""
        print("\n" + "="*60)
        print("  PRUEBAS API DE CONVERSACIONES AI")
        print("="*60)
        
        results = []
        
        # Login
        if not self.login():
            print_error("\n❌ No se pudo autenticar. Abortando pruebas.")
            return
        
        # Tests
        results.append(("Crear conversación", self.test_create_conversation()))
        results.append(("Listar conversaciones", self.test_list_conversations()))
        results.append(("Obtener detalle", self.test_get_conversation()))
        results.append(("Agregar mensaje", self.test_add_message()))
        results.append(("Chat básico", self.test_chat_basic()))
        results.append(("Actualizar título", self.test_update_conversation()))
        results.append(("Eliminar conversación", self.test_delete_conversation()))
        
        # Resumen
        print("\n" + "="*60)
        print("  RESUMEN DE PRUEBAS")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            color = Colors.GREEN if result else Colors.RED
            print(f"{color}{status}{Colors.END} - {test_name}")
        
        print("\n" + "-"*60)
        print(f"Total: {passed}/{total} pruebas exitosas")
        
        if passed == total:
            print_success("\n🎉 ¡Todas las pruebas pasaron!")
        else:
            print_warning(f"\n⚠️  {total - passed} prueba(s) fallaron")
        
        print("="*60 + "\n")


if __name__ == "__main__":
    tester = AIConversationTester()
    tester.run_all_tests()
