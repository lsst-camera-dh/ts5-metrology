from enthought.mayavi.api import Engine
from enthought.tvtk.api import tvtk
import enthought.mayavi.sources.api as sapi
import enthought.mayavi.filters.api as fapi
import enthought.mayavi.modules.api as mapi
from numpy import column_stack

engine = None

class Plot:
    def __init__(self, data, scene, minv, maxv, warp=1, scalarbar=False,
                 points=True, surf=True):
        self.data, self.min, self.max, self.warp = data, minv, maxv, warp
        self.scalarbar = scalarbar
        global engine
        if engine is None: # If Mayavi is not running already
            from enthought.mayavi.api import Engine
            engine = Engine()
            engine.start() # start Mayavi (only works in ipython)
        self.scene = engine.new_scene() if scene is None else scene
        self.source = sapi.VTKDataSource()
        engine.add_source(self.source, scene=self.scene)
        self.update_data()
        if points: self.plot_points()
        if surf: self.plot_surf()
        self.scene.scene.isometric_view()
    
    def update_data(self):
        self.source.data = self.data.as_vtk(warp=self.warp)
        self.source.data_changed = True
    
    def plot_points(self):
        glyph = mapi.Glyph() # Glyph at every point
        glyph.glyph.glyph_source.glyph_source = (glyph.glyph.glyph_source.
                                                 glyph_dict['sphere_source'])
        glyph.glyph.scale_mode = 'data_scaling_off' # Glyphs have constant size
        self.source.add_child(glyph)
    
    def plot_surf(self):
        delaunay = fapi.Delaunay2D() # Triangulate points to obtain a surface
        self.source.add_child(delaunay)
        normals = fapi.PolyDataNormals() # Smooth the triangulation
        normals.filter.splitting = False # Force smoothing of entire surface
        delaunay.add_child(normals)
        elevation = fapi.ElevationFilter() # Color surface based on elevation
        elevation.filter.low_point = [0, 0, self.min*self.warp]
        elevation.filter.high_point = [0, 0, self.max*self.warp]
        elevation.filter.scalar_range = [self.min, self.max]
        normals.add_child(elevation)
        surface = mapi.Surface() # Display the surface
        surface.enable_contours = True
        surface.contour.filled_contours = True
        surface.contour.number_of_contours = 20 # Topographic contours
        elevation.add_child(surface)
        surface.contour.auto_update_range = False
        slm = surface.module_manager.scalar_lut_manager
        slm.use_default_range = False # Use same color range for all tiles
        slm.data_range = [self.min, self.max] # Set global min and max
        slm.show_scalar_bar = self.scalarbar
        outline = mapi.Outline() # Display outline box around the plot
        elevation.add_child(outline)
