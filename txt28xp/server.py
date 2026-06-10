import http.server
import json
import base64
import unicodedata
import textwrap
import sys
from tivars import TIProgram

# Cache for character tokenizability to speed up sanitization
TOKENIZABLE_CACHE = {}

def is_char_supported(char: str) -> bool:
    if char in TOKENIZABLE_CACHE:
        return TOKENIZABLE_CACHE[char]
    
    if char in ('\n', '\r', '\t'):
        TOKENIZABLE_CACHE[char] = True
        return True
        
    try:
        p = TIProgram()
        p.load_string(char)
        TOKENIZABLE_CACHE[char] = True
        return True
    except Exception:
        TOKENIZABLE_CACHE[char] = False
        return False

def sanitize_text(text: str, map_smart_punctuation: bool = True) -> str:
    if map_smart_punctuation:
        # Replace common smart punctuation
        replacements = {
            '“': '"', '”': '"',
            '‘': "'", '’': "'",
            '–': '-', '—': '-',
            '…': '...',
            ' \t': ' ',
        }
        for orig, repl in replacements.items():
            text = text.replace(orig, repl)
            
    # Normalize Unicode characters (decompose accents like é -> e)
    normalized = unicodedata.normalize('NFKD', text)
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    
    # Filter character by character using our cached tokenizer check
    sanitized_chars = []
    for char in ascii_text:
        if char == '\r':
            continue
        if char == '\t':
            sanitized_chars.append(' ')
            continue
        if char == '\n' or is_char_supported(char):
            sanitized_chars.append(char)
            
    return "".join(sanitized_chars)

def wrap_text(text: str, width: int) -> str:
    if width <= 0:
        return text
        
    lines = text.split('\n')
    wrapped_lines = []
    for line in lines:
        if not line.strip():
            wrapped_lines.append('')
            continue
        # Wrap the line
        wrapped = textwrap.wrap(line, width=width, break_long_words=True, break_on_hyphens=False)
        wrapped_lines.extend(wrapped if wrapped else [''])
        
    return '\n'.join(wrapped_lines)

class ConverterRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/convert':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
                raw_text = payload.get('text', '')
                prog_name = payload.get('name', 'NOTES').strip().upper()
                wrap_width = int(payload.get('wrap_width', 0))
                do_sanitize = bool(payload.get('sanitize', True))
                
                # Validate program name
                if not prog_name:
                    prog_name = 'NOTES'
                # Remove non-alphanumeric, limit to 8 chars
                prog_name = "".join(c for c in prog_name if c.isalnum())[:8]
                if not prog_name or not prog_name[0].isalpha():
                    prog_name = 'N' + prog_name[1:]
                    if not prog_name[0].isalpha():
                        prog_name = 'NOTES'
                
                # Process text
                processed_text = raw_text
                if do_sanitize:
                    processed_text = sanitize_text(processed_text)
                if wrap_width > 0:
                    processed_text = wrap_text(processed_text, wrap_width)
                
                # Generate 8xp
                program = TIProgram()
                program.name = prog_name
                program.load_string(processed_text)
                
                file_bytes = program.bytes()
                b64_data = base64.b64encode(file_bytes).decode('utf-8')
                
                response = {
                    'success': True,
                    'filename': f"{prog_name}.8xp",
                    'data': b64_data,
                    'text': processed_text
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {
                    'success': False,
                    'error': str(e)
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def main():
    port = 8000
    server_address = ('', port)
    
    # Warm up token cache for letters/digits to make first conversion fast
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 =+-*/()[]{}.,;:\"'?":
        is_char_supported(c)
        
    httpd = http.server.HTTPServer(server_address, ConverterRequestHandler)
    print(f"Server running on http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == '__main__':
    main()
