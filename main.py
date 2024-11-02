import os
import sys
import time
import subprocess
from pathlib import Path
import shutil

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = f"""{Colors.CYAN}
╭──────────────────────────────────────────╮
│             MP4 → WebM                   │
│        Converter v1.0 By Germanized      │
╰──────────────────────────────────────────╯{Colors.ENDC}"""
    print(banner)

def print_status(message, color=Colors.BLUE):
    print(f"{color}[*] {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.RED}[!] Error: {message}{Colors.ENDC}")

def print_success(message):
    print(f"{Colors.GREEN}[+] {message}{Colors.ENDC}")

def create_progress_bar(progress, total_width=50):
    filled_width = int(total_width * progress / 100)
    bar = '█' * filled_width + '░' * (total_width - filled_width)
    return f"{Colors.CYAN}[{bar}] {progress:.1f}%{Colors.ENDC}"

def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True)
        return True
    except FileNotFoundError:
        return False

def get_video_duration(input_path):
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_path
    ]
    try:
        duration = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode().strip()
        if duration == 'N/A':
            # If stream duration is N/A, try format duration instead
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                input_path
            ]
            duration = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode().strip()
        
        # If we still can't get duration, estimate using bitrate and filesize
        if duration == 'N/A':
            return None
            
        return float(duration)
    except:
        return None

def convert_video(input_path):
    try:
        # Get terminal width for centering
        terminal_width = shutil.get_terminal_size().columns

        clear_screen()
        print_banner()
        
        # Validate input file
        if not os.path.exists(input_path):
            print_error("Input file not found!")
            return False
            
        print_status("Starting conversion process...")
        print_status(f"Input file: {Colors.YELLOW}{input_path}{Colors.ENDC}")
        
        # Create output path
        output_path = str(Path(input_path).with_suffix('.webm'))
        print_status(f"Output will be saved as: {Colors.YELLOW}{output_path}{Colors.ENDC}")
        
        # Get video duration for progress calculation
        duration = get_video_duration(input_path)
        if duration is None:
            print_status("Could not determine video duration. Progress bar will show frames processed.", Colors.YELLOW)
            duration = 1  # Use dummy duration for progress calculation
        
        # Prepare conversion command
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-progress', 'pipe:1',
            '-c:v', 'libvpx-vp9',
            '-crf', '30',
            '-b:v', '0',
            '-c:a', 'libopus',
            '-y',  # Overwrite output file if exists
            output_path
        ]
        
        # Start conversion process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        print("\n")  # Add space for progress bar
        frame_count = 0
        
        while True:
            line = process.stdout.readline()
            
            if not line and process.poll() is not None:
                break
                
            if 'frame=' in line:
                try:
                    frame = line.split('frame=')[1].strip()
                    if frame.isdigit():
                        frame_count = int(frame)
                        # Show frame count if duration is unknown
                        if duration == 1:
                            progress_text = f"Processed {frame_count} frames"
                            sys.stdout.write('\033[F')  # Move cursor up
                            sys.stdout.write('\033[K')  # Clear line
                            print(progress_text.center(terminal_width))
                            continue
                except:
                    pass
                    
            if 'out_time_ms=' in line:
                try:
                    time_ms = int(line.split('=')[1]) / 1000000
                    progress = (time_ms / duration) * 100 if duration != 1 else 0
                    
                    # Clear previous line and print progress
                    sys.stdout.write('\033[F')  # Move cursor up
                    sys.stdout.write('\033[K')  # Clear line
                    progress_bar = create_progress_bar(progress)
                    print(progress_bar.center(terminal_width))
                except:
                    pass
        
        # Check conversion result
        if process.returncode == 0 and os.path.exists(output_path):
            print("\n")  # Add space after progress bar
            print_success("Conversion completed successfully!")
            print_success(f"Output saved to: {Colors.YELLOW}{output_path}{Colors.ENDC}")
            return True
        else:
            stderr_output = process.stderr.read()
            print_error(f"Conversion failed! FFmpeg error: {stderr_output}")
            return False
            
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        return False

def main():
    clear_screen()
    print_banner()
    
    # Check for FFmpeg installation
    if not check_ffmpeg():
        print_error("FFmpeg is not installed or not found in system PATH!")
        print_status("Please install FFmpeg to use this converter.", Colors.YELLOW)
        return
    
    # Get input file
    print(f"{Colors.YELLOW}Enter the path to your MP4 file:{Colors.ENDC}")
    input_path = input(f"{Colors.CYAN}> {Colors.ENDC}").strip()
    
    # Remove quotes if present
    input_path = input_path.strip('"\'')
    
    # Start conversion
    convert_video(input_path)
    
    print(f"\n{Colors.YELLOW}Press Enter to exit...{Colors.ENDC}")
    input()

if __name__ == "__main__":
    main()