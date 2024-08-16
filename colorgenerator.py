

class ColorGenerator: # This class is used to generate colors from an image
    
    def __init__(self,image):
        self.colors = []
        self.image = image
        
    def generate_colors(self):
        self.colors = self.image.convert('RGB').getcolors(maxcolors=1000000) # Get all colors from the image
        self.colors.sort(key=lambda x: x[0],reverse=True) # Sort the colors by count in descending order
        return self.colors
    
