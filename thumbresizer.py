import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageOps, ImageFilter

class ThumbnailResizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Otimizador de Thumbnails")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # Variáveis
        self.folder_path = tk.StringVar()
        self.progress = tk.DoubleVar()
        self.status = tk.StringVar(value="Pronto para começar")
        self.is_processing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="Otimizador de Thumbnails", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Seletor de pasta
        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(folder_frame, text="Pasta:").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Entry(folder_frame, textvariable=self.folder_path).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(folder_frame, text="Procurar", command=self.browse_folder).pack(side=tk.LEFT)
        
        # Informações
        info_frame = ttk.LabelFrame(main_frame, text="Informações", padding="10")
        info_frame.pack(fill=tk.X, pady=10)
        
        info_text = """• Procura por arquivos 'thumbnail.png' em todas as subpastas
• Reduz o tamanho pela metade
• Aplica otimização automática de qualidade  
• Substitui os arquivos originais (sem backup)
• Formatos suportados: PNG, JPG, JPEG
• Suporte a imagens com transparência (RGBA)"""
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(anchor=tk.W)
        
        # Área de status
        status_frame = ttk.LabelFrame(main_frame, text="Progresso", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Barra de progresso
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Status text
        status_label = ttk.Label(status_frame, textvariable=self.status)
        status_label.pack(anchor=tk.W)
        
        # Log
        log_frame = ttk.Frame(status_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame dos botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=15)
        
        # Botões centralizados
        self.process_btn = ttk.Button(button_frame, text="Iniciar Processamento", 
                                     command=self.start_processing)
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Limpar Log", 
                  command=self.clear_log).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Sair", 
                  command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Selecione a pasta principal")
        if folder:
            self.folder_path.set(folder)
            self.log(f"Pasta selecionada: {folder}")
            
    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        
    def process_thumbnail(self, file_path):
        try:
            with Image.open(file_path) as img:
                # Calcula metade do tamanho original
                new_size = (img.width // 2, img.height // 2)
                
                # Reduz a imagem usando LANCZOS para alta qualidade
                resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Verifica o modo da imagem e aplica otimização apropriada
                if resized_img.mode == 'RGBA':
                    # Para imagens com transparência, aplica um sharpening leve
                    optimized_img = resized_img.filter(ImageFilter.SHARPEN)
                elif resized_img.mode in ['RGB', 'L']:
                    # Para RGB e escala de cinza, aplica autocontrast
                    optimized_img = ImageOps.autocontrast(resized_img, cutoff=2)
                else:
                    # Para outros modos, converte para RGB e aplica autocontrast
                    optimized_img = resized_img.convert('RGB')
                    optimized_img = ImageOps.autocontrast(optimized_img, cutoff=2)
                
                # Substitui a imagem original sem backup
                if file_path.lower().endswith('.png'):
                    # Preserva a transparência para PNG
                    optimized_img.save(file_path, optimize=True)
                else:
                    optimized_img.save(file_path, optimize=True, quality=85)
                
            return True, f"✓ Processado: {file_path}"
            
        except Exception as e:
            return False, f"✗ Erro em {file_path}: {str(e)}"
    
    def find_thumbnails(self, folder_path):
        thumbnails = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower() == 'thumbnail.png':
                    thumbnails.append(os.path.join(root, file))
                elif file.lower() in ['thumbnail.jpg', 'thumbnail.jpeg']:
                    thumbnails.append(os.path.join(root, file))
        return thumbnails
    
    def processing_thread(self):
        folder = self.folder_path.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Erro", "Selecione uma pasta válida!")
            return
            
        self.is_processing = True
        self.process_btn.config(state='disabled')
        
        try:
            # Encontrar todos os thumbnails
            self.status.set("Procurando thumbnails...")
            self.log("Procurando por arquivos thumbnail...")
            thumbnails = self.find_thumbnails(folder)
            
            if not thumbnails:
                self.log("Nenhum arquivo thumbnail encontrado!")
                self.status.set("Nenhum thumbnail encontrado")
                return
                
            self.log(f"Encontrados {len(thumbnails)} arquivos para processar")
            
            # Processar cada thumbnail
            processed = 0
            errors = 0
            
            for i, thumbnail in enumerate(thumbnails):
                if not self.is_processing:
                    break
                    
                # Atualizar progresso
                progress_percent = (i / len(thumbnails)) * 100
                self.progress.set(progress_percent)
                self.status.set(f"Processando {i+1}/{len(thumbnails)}")
                
                # Processar arquivo
                success, message = self.process_thumbnail(thumbnail)
                self.log(message)
                
                if success:
                    processed += 1
                else:
                    errors += 1
                
                self.root.update_idletasks()
            
            # Finalizar
            self.progress.set(100)
            self.status.set(f"Concluído! {processed} processados, {errors} erros")
            self.log(f"Processamento concluído! Sucessos: {processed}, Erros: {errors}")
            
            if errors == 0:
                messagebox.showinfo("Concluído", f"Processamento completo!\n{processed} arquivos otimizados com sucesso!")
            else:
                messagebox.showwarning("Concluído", f"Processamento completo!\n{processed} arquivos otimizados\n{errors} erros encontrados")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro durante o processamento: {str(e)}")
            self.log(f"ERRO: {str(e)}")
        finally:
            self.is_processing = False
            self.process_btn.config(state='normal')
    
    def start_processing(self):
        if not self.folder_path.get():
            messagebox.showwarning("Aviso", "Selecione uma pasta primeiro!")
            return
            
        if self.is_processing:
            return
            
        # Confirmar ação
        result = messagebox.askyesno(
            "Confirmar", 
            "ATENÇÃO: Isso substituirá todos os arquivos thumbnail originais SEM BACKUP!\n\nDeseja continuar?"
        )
        
        if result:
            # Limpar log anterior
            self.clear_log()
            self.progress.set(0)
            
            # Executar em thread separada para não travar a UI
            thread = threading.Thread(target=self.processing_thread)
            thread.daemon = True
            thread.start()

def main():
    try:
        from PIL import Image, ImageOps, ImageFilter
    except ImportError:
        print("Pillow não está instalado. Instale com: pip install pillow")
        return
        
    root = tk.Tk()
    app = ThumbnailResizer(root)
    root.mainloop()

if __name__ == "__main__":
    main()