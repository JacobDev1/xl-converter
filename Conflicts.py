# This class checks If formats are compatible with each other.

class Conflicts():
    def __init__(self):
        self.conflict = False
        self.conflict_msg = []

        self.jxl_conflict = False
        self.jxl_e = None
        self.jxl_int_e = None
    
    def checkForConflicts(self, ext, _format, int_e, effort, downscaling):
        """
        Arguments:
            ext - source extension
            _format - format to convert to
            int_e - intelligent effort enabled
            effort - effort
            downscaling - downscaling enabled
        """
        if ext in ("gif", "apng"):
            self.conflict = True

            # Animation
            match ext:
                case "gif":
                    if _format in ("JPEG XL", "WEBP", "PNG"):
                        self.conflict = False
                case "apng":
                    if _format in ("JPEG XL"):
                        self.conflict = False
            
            if self.conflict:
                self.conflict_msg.append(f"Animation is not supported for {_format} - stopped the process")

            # Intelligent Effort
            if _format == "JPEG XL":
                if int_e:
                    self.jxl_int_e = False
                    self.jxl_e = 7
                    self.jxl_conflict = True
                    self.conflict_msg.append(f"Intelligent effort is not compatible with {ext.upper()} - defaulted to 7")
                elif effort > 7:   # Efforts bigger than 7 cause the encoder to crash while processing APNGs
                    self.jxl_e = 7
                    self.jxl_conflict = True
                    self.conflict_msg.append(f"Efforts bigger than 7 are not compatible with {ext.upper()} - defaulted to 7")

            # Downscaling
            if downscaling:
                self.conflict = True
                self.conflict_msg.append(f"Downscaling is not supported for animation - stopped the process")
        else:
            self.conflict = False
        
        return self.conflict

    def conflictOccured(self):
        return self.conflict

    def getConflictsMsg(self):
        return self.conflict_msg

    def jxlConflictOccured(self):
        return self.jxl_conflict
    
    def jxlGetNormEffort(self, effort):
        if self.jxl_conflict == None or self.jxl_e == None:
            return effort
        
        return self.jxl_e

    def jxlGetNormIntEffort(self, int_e):
        if self.jxl_conflict == None or self.jxl_int_e == None:
            return int_e

        return self.jxl_int_e