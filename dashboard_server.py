#!/usr/bin/env python3
"""
Servidor web simples para o dashboard Job Radar.
Uso: python dashboard_server.py [porta]
Acede: http://localhost:8080
"""
import os
import sys
import glob
from http.server import HTTPServer, SimpleHTTPRequestHandler

class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Redirect "/" para o último dashboard gerado
        if self.path in ('/', ''):
            html_files = sorted(glob.glob('jobs_*.html'), key=os.path.getmtime, reverse=True)
            if html_files:
                self.path = f'/{html_files[0]}'
                # Redirect 302
                self.send_response(302)
                self.send_header('Location', self.path)
                self.end_headers()
                return
            else:
                self.send_error(404, "Nenhum dashboard encontrado. Corre primeiro: python job_radar.py")
                return
        return super().do_GET()

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    server = HTTPServer(('127.0.0.1', port), DashboardHandler)
    print(f"🌐 Dashboard disponível em: http://localhost:{port}")
    print(f"   Pasta: {os.getcwd()}")
    print(f"   Ctrl+C para parar\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Servidor parado")
        server.shutdown()

if __name__ == '__main__':
    main()
