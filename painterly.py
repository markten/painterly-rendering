import numpy as np
from math import sqrt, floor
from PIL import Image, ImageFilter
from scipy import ndimage
from random import shuffle
import cairo
import logging
from os import path

THRESHOLD = 10
GRID_SIZE = 1
MIN_STROKE_LEN = 4
MAX_STROKE_LEN = 16

class Painting:

    def __init__(self, filepath):
        
        self.source_filename = None
        self.surface = None
        self.ctx = None
        
        self.source_img = None
        self.reference_img = None
        self.difference_img = None
        self.gradient_x = None
        self.gradient_y = None
        self.edge_img = None
        self.canvas = None
        self.canvas_pix = None
        self.reference_img_pix = None
    
        
        self.source_filename = path.basename(filepath).split('.')[0]
        self.source_img = Image.open(filepath).convert('RGB')
        self.make_draw_surface(self.source_img.width, self.source_img.height)
        
    def make_draw_surface(self, width, height):
        self.surface = cairo.ImageSurface (cairo.FORMAT_RGB24, width, height)
        self.ctx = cairo.Context(self.surface)
        self.ctx.scale(width, height)
        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.surface_to_canvas()
        
    def render(self, radii, save_layers):
        layer_num = 0
        
        # iterate over brush sizes
        for radius in radii:
            
            logging.info("\tPainting with radius: " + str(radius) + "px")
            
            # generate reference image (apply gaussian blur)
            logging.info("\t\tBlurring image...")        
            self.reference_img = self.source_img.filter(ImageFilter.GaussianBlur(radius=radius))
            
            # paint a layer with a single brush radius
            self.paint_layer(radius)
            
            if save_layers:
                self.surface.write_to_png (self.source_filename + "_layer_" + str(layer_num) + ".png")
            
            self.surface_to_canvas()
            
            layer_num += 1
    
    def surface_to_canvas(self):
        # cairo surface data is stored in a different order than a pillow image
        # some array restructuring is done for the conversion
        
        if self.surface.get_format() == cairo.FORMAT_RGB24:
            surface_data = np.array(self.surface.get_data())
            surface_data.shape = (self.surface.get_height(), self.surface.get_width(), 4)
            surface_data = np.dstack((
                surface_data[:,:,2],
                surface_data[:,:,1],
                surface_data[:,:,0]))
            
            self.canvas = Image.fromarray(surface_data)
            
        else:
            logging.error("Cairo surface of improper type to convert to Pillow image.")
    
    def paint_layer(self, radius):
    
        width = self.surface.get_width()
        height = self.surface.get_height()
        
        strokes = []
        
        logging.info("\t\tCalculating image difference...")
        self.difference_img = image_diff(self.reference_img, self.canvas)
        
        # define a grid step based on stroke radius
        grid = GRID_SIZE * radius
        
        x_grid = np.arange(0, (width//grid)*grid, grid)
        y_grid = np.arange(0, (height//grid)*grid, grid)
        
        # calculate the error of the grid section
        for x in x_grid:
            for y in y_grid:
                section = self.difference_img[y:y+grid, x:x+grid]
                total_error = section.sum() // (grid**2)
                                
                if (total_error > THRESHOLD or radius == 64):
                    section = section.reshape((grid, grid))
                    max_coord = np.argmax(section)
                    max_coord = (x+(max_coord%grid), y+(max_coord//grid))
                    stroke = Stroke(max_coord)
                    strokes.append(stroke)
        
        logging.info("\t\t" + "Strokes: " + str(len(strokes)))
        
        logging.info("\t\tEdge detection...")
        luminanceImage = np.asarray(self.reference_img.convert(mode='I')).reshape(((height, width)))
        self.gradient_x = ndimage.sobel(luminanceImage, 0)
        self.gradient_y = ndimage.sobel(luminanceImage, 1)
        self.edge_img = np.hypot(self.gradient_x, self.gradient_y)
        
        self.reference_img_pix = np.asarray(self.reference_img)
        self.reference_img_pix = self.reference_img_pix.reshape((height, width, 3))
        self.canvas_pix = np.asarray(self.canvas).reshape((height, width, 3))
        
        shuffle(strokes)
        
        logging.info("\t\tPainting strokes...")
        for stroke in strokes:
            self.calc_stroke(stroke, radius)
            stroke.cairo_convert(width, height)
            self.paint_stroke(stroke, radius)

    def calc_stroke(self, stroke, radius):
        
        x = int(stroke.points[0][0])
        y = int(stroke.points[0][1])
        
        stroke.color = tuple(self.reference_img_pix[y,x,:])
        
        last_dx = 0
        last_dy = 0
        
        for stroke_length in range(1, MAX_STROKE_LEN+1):
            
            if (stroke_length > MIN_STROKE_LEN and
                abs(pixel_diff(self.reference_img_pix[y,x,:], self.canvas_pix[y,x,:])) <
                abs(pixel_diff(self.reference_img_pix[y,x,:], stroke.color))):
                break
                
            if (self.edge_img[y,x] == 0):
                break
                
            gx = self.gradient_x[y,x]
            gy = self.gradient_y[y,x]
            dx = -gy
            dy = gx

            if (last_dx * dx + last_dy * dy < 0):
                dx = -dx
                dy = -dy
            
            denom = sqrt(dx**2 + dy**2)
            dx = dx / denom
            dy = dy / denom
            
            x = abs(floor(x+radius*dx))
            y = abs(floor(y+radius*dy))
            
            if x > self.canvas_pix.shape[1]-1 or y > self.canvas_pix.shape[0]-1:
                break
            
            last_dx = dx
            last_dy = dy
            
            stroke.points.append((x,y))

    def paint_stroke(self, stroke, radius):
        
        self.ctx.set_line_width(max(self.ctx.device_to_user_distance(2*radius, 2*radius)))
        self.ctx.set_source_rgb(stroke.color[0]/255,stroke.color[1]/255,stroke.color[2]/255) # Solid color
        
        if len(stroke.points) > 1:
            for index in range(len(stroke.points)-1):
                self.ctx.move_to(stroke.points[index][0], stroke.points[index][1])
                self.ctx.line_to(stroke.points[index+1][0], stroke.points[index+1][1])
        else:
            points = stroke.points[0]
            if radius == 64:
                self.ctx.set_line_width(max(self.ctx.device_to_user_distance(10*radius, 10*radius)))
            self.ctx.move_to(stroke.points[0][0], stroke.points[0][1])
        
        self.ctx.close_path()
        self.ctx.stroke()
        
    def save(self, filepath=None):
    
        if not filepath:
            filepath = self.source_filename + "_painterly.png"
        
        print('Saved as: ' + filepath)
        self.surface.write_to_png(filepath)
        
def pixel_diff(a, b):
    diff = sqrt(((int(a[0])-int(b[0])) ** 2)
               +((int(a[1])-int(b[1])) ** 2)
               +((int(a[2])-int(b[2])) ** 2))
    return diff
        
def image_diff(img_a, img_b):
    
    width, height = img_a.size
    
    # convert images to numpy arrays
    array_a = np.asarray(img_a)
    array_b = np.asarray(img_b)
    
    # calculate distance
    array_diff = array_a - array_b
    array_diff = array_diff**2
    array_diff = array_diff.reshape(height, width, 3)
    array_diff = np.sum(array_diff, axis=2)
    array_diff = np.sqrt(array_diff)
    
    return array_diff

class Stroke:

    def __init__(self, coord):
        self.points = [coord]
        self.color = None

    def cairo_convert(self, width, height):
        
        cairo_points = []
    
        for point in self.points:
            cairo_points.append((point[0]/width,point[1]/height))
            
        self.points = cairo_points
