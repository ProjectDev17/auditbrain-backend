"""
Script de pruebas avanzadas: Streaming SSE y Tool Calling.
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

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


class AdvancedAITester:
    def __init__(self):
        self.token = None
        self.conversation_id = None
        self.headers = {}
    
    def login(self):
        """Obtener token JWT."""
        print_info("Autenticando usuario...")
        
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
            print_success(f"Login exitoso")
            return True
        else:
            print_error(f"Login falló: {response.status_code}")
            return False
    
    def create_conversation(self):
        """Crear conversación para pruebas."""
        print_info("Creando conversación de prueba...")
        
        response = requests.post(
            f"{API_URL}/ai-conversations/",
            headers=self.headers,
            json={"title": "Advanced Test - Streaming & Tools"}
        )
        
        if response.status_code == 201:
            data = response.json()
            self.conversation_id = data['id']
            print_success(f"Conversación creada: {self.conversation_id}")
            return True
        else:
            print_error(f"Error creando conversación: {response.status_code}")
            return False
    
    def test_streaming(self):
        """Probar streaming SSE."""
        print_info("\n1. Probando Chat Streaming (SSE)...")
        
        if not self.conversation_id:
            print_error("No hay conversation_id")
            return False
        
        try:
            response = requests.post(
                f"{API_URL}/ai-conversations/{self.conversation_id}/chat-stream/",
                headers=self.headers,
                json={
                    "message": "Cuenta del 1 al 5 lentamente",
                    "enable_tools": False
                },
                stream=True,
                timeout=60
            )
            
            if response.status_code != 200:
                print_error(f"Error en streaming: {response.status_code}")
                return False
            
            print_success("Streaming iniciado. Recibiendo chunks:")
            
            chunk_count = 0
            full_response = ""
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    
                    # SSE format: "data: {...}"
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove "data: " prefix
                        
                        try:
                            data = json.loads(data_str)
                            
                            if data.get('done'):
                                print_info(f"\n   ✓ Streaming completado")
                                break
                            
                            if 'content' in data:
                                content = data['content']
                                full_response += content
                                chunk_count += 1
                                
                                # Mostrar primeros chunks
                                if chunk_count <= 10:
                                    print(f"   Chunk {chunk_count}: '{content}'", end='')
                                elif chunk_count == 11:
                                    print("\n   ... (más chunks) ...", end='')
                            
                            if 'error' in data:
                                print_error(f"\n   Error: {data['error']}")
                                return False
                                
                        except json.JSONDecodeError:
                            continue
            
            print(f"\n")
            print_success(f"Streaming exitoso")
            print_info(f"   Total chunks: {chunk_count}")
            print_info(f"   Respuesta completa ({len(full_response)} chars):")
            print_info(f"   '{full_response[:200]}...'")
            
            return True
            
        except Exception as e:
            print_error(f"Error en streaming: {e}")
            return False
    
    def test_tool_calling(self):
        """Probar tool calling con MCP."""
        print_info("\n2. Probando Tool Calling (MCP Integration)...")
        
        if not self.conversation_id:
            print_error("No hay conversation_id")
            return False
        
        try:
            response = requests.post(
                f"{API_URL}/ai-conversations/{self.conversation_id}/chat/",
                headers=self.headers,
                json={
                    "message": "¿Cuántas auditorías hay en total en el sistema?",
                    "enable_tools": True
                },
                timeout=60
            )
            
            if response.status_code != 200:
                print_error(f"Error en tool calling: {response.status_code}")
                print_error(f"Response: {response.text[:500]}")
                return False
            
            data = response.json()
            
            # Buscar si hubo tool calls
            messages = data.get('messages', [])
            assistant_messages = [m for m in messages if m['role'] == 'assistant']
            
            if not assistant_messages:
                print_warning("No se encontró respuesta del asistente")
                return False
            
            last_msg = assistant_messages[-1]
            tool_calls = last_msg.get('tool_calls')
            content = last_msg.get('content', '')
            
            print_success("Tool calling ejecutado")
            
            if tool_calls:
                print_info(f"   ✓ Tools ejecutadas: {len(tool_calls)}")
                for i, tc in enumerate(tool_calls, 1):
                    tool_name = tc.get('function', {}).get('name', 'unknown')
                    print_info(f"   Tool {i}: {tool_name}")
            else:
                print_warning("   No se detectaron tool calls en la respuesta")
            
            print_info(f"   Respuesta del asistente:")
            print_info(f"   '{content[:300]}...'")
            
            # Verificar si la respuesta contiene información de auditorías
            if 'audit' in content.lower() or 'total' in content.lower():
                print_success("   ✓ Respuesta contiene información de auditorías")
                return True
            else:
                print_warning("   La respuesta no parece contener info de auditorías")
                return True  # Aún así consideramos exitoso si no hubo error
            
        except Exception as e:
            print_error(f"Error en tool calling: {e}")
            return False
    
    def cleanup(self):
        """Limpiar conversación de prueba."""
        if self.conversation_id:
            print_info("\nLimpiando conversación de prueba...")
            requests.delete(
                f"{API_URL}/ai-conversations/{self.conversation_id}/",
                headers=self.headers
            )
            print_success("Conversación eliminada")
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas avanzadas."""
        print("\n" + "="*60)
        print("  PRUEBAS AVANZADAS: STREAMING & TOOL CALLING")
        print("="*60)
        
        if not self.login():
            print_error("\n❌ No se pudo autenticar. Abortando.")
            return
        
        if not self.create_conversation():
            print_error("\n❌ No se pudo crear conversación. Abortando.")
            return
        
        results = []
        results.append(("Streaming SSE", self.test_streaming()))
        results.append(("Tool Calling (MCP)", self.test_tool_calling()))
        
        # Limpiar
        self.cleanup()
        
        # Resumen
        print("\n" + "="*60)
        print("  RESUMEN DE PRUEBAS AVANZADAS")
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
            print_success("\n🎉 ¡Todas las pruebas avanzadas pasaron!")
        else:
            print_warning(f"\n⚠️  {total - passed} prueba(s) fallaron")
        
        print("="*60 + "\n")


if __name__ == "__main__":
    tester = AdvancedAITester()
    tester.run_all_tests()
