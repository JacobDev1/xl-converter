import re, os, random

class Pathing():
    def __init__(self):
        pass

    def getUniqueFilePath(self, dir, file_name: str, ext: str, add_rnd = False):
        """Get a unique file name within a directory."""

        # Generate Random String
        rnd = ""
        if add_rnd:
            for i in range(3):
                rnd += str(hex(random.randint(0, 0xf)))[2:]  # Yes, it's random and a hex number. There are no actual words generated.
        
        # Setup Path
        path = ""
        if add_rnd:
            path = os.path.join(dir,f"{file_name}_{rnd}.{ext}")
        else:
            path = os.path.join(dir,f"{file_name}.{ext}")

        # Check for uniqueness
        n = 1
        
        prev = re.search(r"\([0-9]{1,}\)$", file_name)  # Detect a previously renamed file
        if prev != None:
            n = int(prev.group(0)[1:-1])    # Parse previously assigned number

        while os.path.isfile(path):
            if add_rnd:
                path = os.path.join(dir,f"{file_name}_{rnd}.{ext}")
            else:
                if prev != None and len(file_name) > len(prev.group(0)):
                    spacing = "" if file_name[len(file_name) - len(prev.group(0)) - 1] != " " else ""  # Add spacing to "file(1)", not "file (1)"
                    path = os.path.join(dir,f"{file_name[:-len(prev.group(0))]}{spacing}({n}).{ext}")
                else:
                    path = os.path.join(dir,f"{file_name} ({n}).{ext}")
            n += 1
        return path
    
    def getPathGIF(self, output_dir, item_name, mode):
        """Single-purpose method for decoding GIF to PNG with ImageMagick."""
        new_path = os.path.join(output_dir, f"{item_name}.png")
        match mode:
            case "Rename":
                if os.path.isfile(os.path.join(output_dir, f"{item_name}-0.png")):
                    n = 0
                    while os.path.isfile(os.path.join(output_dir, f"{item_name} ({n})-0.png")):
                        n += 1
                    new_path = os.path.join(output_dir, f"{item_name} ({n}).png")
                return new_path
            case "Replace":
                return new_path
    
    def getExtension(self, _format):
        """Get file extension for the specified format."""
        match _format :
            case "JPEG XL":
                return "jxl"
            case "PNG":
                return "png"
            case "AVIF":
                return "avif"
            case "WEBP":
                return "webp"
            case "JPG":
                return "jpg"
            case "Smallest Lossless":   # Handled in Worker
                return None
            case _:
                print(f"[Pathing - getExtension()] No extension declared for {_format}")