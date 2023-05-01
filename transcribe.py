import torch
import time
import whisper
import os

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import argparse


class WavDetectorHandler(FileSystemEventHandler):
    def __init__(self, translator):
        self.translator = translator

    def on_created(self, event):
        if not event.is_directory:
            self.translator.translate(event.src_path)

class PostAction:
    def __init__(self, destination=None, delete=False):
        self.destination = destination
        self.delete = delete
        
    def post_action(self, file_path):
        if self.delete:
           os.remove(file_path)
        elif self.destination is not None:
           shutil.move(file_path, self.destination)

class WhisperTranslator:
    def __init__(self, model_name, fp16=False, output_path=None, pipe_path=None, post_action=None, verbose=False):
        self.device = torch.device('cuda')
        self.model = whisper.load_model(name=model_name, device=self.device)
        self.fp16 = fp16
        self.post_action = post_action
        self.verbose = verbose
        self.output_path = output_path        
        self.pipe_path = pipe_path
        if output_path and pipe_path:
            raise ValueError("output_path and pipe_path are mutually exclusive")

    def load_whisper_model(self, model_name):
        self.model = whisper.load_model(name=model_name, device=self.device)

    def translate(self, file_path):
        if self.verbose: print(f"Got #{file_path} ");
        audio = whisper.load_audio(file_path, sr=16000)
        result = self.model.transcribe(audio, language='en', task='transcribe', fp16=self.fp16)

        if self.verbose: print(f"Got #{result['text']} ");
        if self.output_path:
            dir_path, file_name = os.path.split(file_path)
            file_base, file_ext = os.path.splitext(file_name)
            output_file = os.path.join(self.output_path, f"{file_base}.txt")
            with open(output_file, 'w') as f:
                f.write(result['text'])
        elif self.pipe_path:
            with open(self.pipe_path, 'w') as f:
                f.write(result,['text'])
        else:
            print(f"#{result['text']}\n")
            
        if post_action is not None:
            post_action.post_action(file_path)

def watch_dir():
    event_handler = WavDetectorHandler(translator=translator)
    print("Event Handler created")
    observer = Observer()
    observer.schedule(event_handler, args.wav_path, recursive=True)
    observer.start()

    # Start watching directory
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def translate_dir(d, r , translator):
    c = len(os.listdir(d))
    while c > 0:
     for filename in os.listdir(d):
      if filename.endswith(".wav"):
        filepath = os.path.join(d, filename)
        translator.translate(filepath)
     if r == False:
      c = 0
     else:
      c = len(os.listdir(d))
      
def main():

    parser = argparse.ArgumentParser(description="Whisper Translator Command Line Arguments")
    parser.add_argument("model_name", help="The name of the Whisper model to use. tiny|base|small|medium")
    parser.add_argument("-f", "--fp16", action="store_true", help="Enable mixed-precision inference. 16 not always faster 32 better on maxwell")
    parser.add_argument("-w", "--wav-path", help="The path to the input directorty of WAVs to transcribe.")
    parser.add_argument("-o", "--output-path", help="The directory path to write the output transcript files.")
    parser.add_argument("-p", "--pipe-path", help="The path to the named pipe to write the output transcript to.")
    parser.add_argument("-W", "--watch", action="store_true", help="Watch the wav_path and transcbribe files as they appear.")
    parser.add_argument("-D", "--delete", action="store_true", help="Delete the wave files once they are processed")
    parser.add_argument("-m", "--move-to-dir", help="Move wav files once they are processed to this dir`")
    parser.add_argument("-r", "--recursive", action="store_true", help="Run until all wavs files are processed, not just the ones present on run`")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output`")
    args = parser.parse_args()

    post_action = PostAction(args.move_to_dir,args.delete)
    
    if args.verbose: print("Starting translation services")

    translator = WhisperTranslator(
        model_name=args.model_name,
        fp16=args.fp16,
        output_path=args.output_path,
        pipe_path=args.pipe_path,
        post_action=post_action,
        verbose = args.verbose
    )
    
    if args.verbose: print(f"Translator Model loaded using model #{args.model_name}") 

    translate_dir(args.wav_path, args.recursive, translator) 

    if args.watch == True:
        if args.verbose: print(f"Watching Dir #{args.wav_path}")
        watch_dir()
    # Set up WavDetectorHandler


if __name__ == "__main__":
    main()
          
