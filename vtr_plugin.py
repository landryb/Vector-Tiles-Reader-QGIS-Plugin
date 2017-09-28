# -*- coding: utf-8 -*-

""" THIS COMMENT MUST NOT REMAIN INTACT

GNU GENERAL PUBLIC LICENSE

Copyright (c) 2017 geometalab HSR

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

"""

from log_helper import debug, info, warn, critical
from PyQt4.QtCore import *  # QSettings, QTimer, QueuedConnection
from PyQt4.QtGui import *  # QAction, QIcon, QMenu, QToolButton,  QMessageBox, QColor, QFileDialog
from qgis.core import *
from qgis.gui import QgsMessageBar

from file_helper import FileHelper
from tile_helper import get_tile_bounds, epsg3857_to_wgs84_lonlat, tile_to_latlon, latlon_to_tile
from ui.dialogs import AboutDialog, ProgressDialog, ConnectionsDialog

import os
import sys
import site
import traceback
import json


class VtrPlugin:
    _dialog = None
    _model = None
    _reload_button_text = "Load features overlapping the view extent"
    add_layer_action = None

    zoom_level_by_lower_scale_bound = {
        1000000000: 0,
        500000000: 1,
        200000000: 2,
        50000000: 3,
        25000000: 4,
        12500000: 5,
        6500000: 6,
        3000000: 7,
        1500000: 8,
        750000: 9,
        400000: 10,
        200000: 11,
        100000: 12,
        50000: 13,
        25000: 14,
        12500: 15,
        5000: 16,
        2500: 17,
        1500: 18,
        750: 19,
        500: 20,
        250: 21,
        100: 22,
        0: 23
    }

    def _get_zoom_for_current_map_scale(self):
        current_scale = self._get_current_map_scale()
        return self._get_zoom_for_scale(current_scale)

    def _get_current_map_scale(self):
        canvas = self.iface.mapCanvas()
        current_scale = canvas.scale()
        return current_scale

    def _get_zoom_for_scale(self, scale):
        if scale < 0:
            scale = 0
        zoom = 0
        for lower_bound in sorted(self.zoom_level_by_lower_scale_bound, key=lambda k: k*-1):
            if scale > lower_bound:
                zoom = self.zoom_level_by_lower_scale_bound[lower_bound]
                break
        return zoom

    def __init__(self, iface):
        self.iface = iface
        self._add_path_to_dependencies_to_syspath()
        self.settings = QSettings("Vector Tile Reader", "vectortilereader")
        self.connections_dialog = ConnectionsDialog(FileHelper.get_sample_data_directory())
        self.connections_dialog.on_connect.connect(self._on_connect)
        self.connections_dialog.on_add.connect(self._on_add_layer)
        self.connections_dialog.on_zoom_change.connect(self._update_nr_of_tiles)
        self.progress_dialog = None
        self._current_reader = None
        self._current_writer = None
        self._current_options = None
        self._add_path_to_icons()
        self._current_layer_filter = []
        self._auto_zoom = False
        self._current_zoom = None
        self._current_scale = None
        self._scale_change_connected = False
        self._loaded_scale = None
        self._is_loading = False
        self.iface.mapCanvas().xyCoordinates.connect(self._handle_mouse_move)
        self._map_scale_timer = QTimer()
        self._map_scale_timer.timeout.connect(self._handle_scale_change_delayed)
        self._connect_map_refresh()

    def initGui(self):
        self.popupMenu = QMenu(self.iface.mainWindow())
        self.open_connections_action = self._create_action("Add Vector Tiles Layer...", "server.svg",
                                                           self._show_connections_dialog)
        self.reload_action = self._create_action(self._reload_button_text, "reload.svg", self._reload_tiles, False)
        self.export_action = self._create_action("Export selected layers", "save.svg", self._export_tiles)
        self.clear_cache_action = self._create_action("Clear cache", "delete.svg", FileHelper.clear_cache)
        self.about_action = self._create_action("About", "info.svg", self.show_about)
        self.iface.insertAddLayerAction(self.open_connections_action)  # Add action to the menu: Layer->Add Layer
        self.popupMenu.addAction(self.open_connections_action)
        self.popupMenu.addAction(self.reload_action)
        self.popupMenu.addAction(self.export_action)
        self.popupMenu.addAction(self.clear_cache_action)
        self.popupMenu.addAction(self.about_action)
        self.toolButton = QToolButton()
        self.toolButton.setMenu(self.popupMenu)
        self.toolButton.setDefaultAction(self.open_connections_action)
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolButtonAction = self.iface.layerToolBar().addWidget(self.toolButton)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.open_connections_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.reload_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.export_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.clear_cache_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.about_action)
        info("Vector Tile Reader Plugin loaded...")

    def _connect_map_refresh(self):
        if not self._scale_change_connected:
            self.iface.mapCanvas().scaleChanged.connect(self._on_map_refresh, Qt.QueuedConnection)
            self._scale_change_connected = True

    def _disconnect_map_refresh(self):
        if self._scale_change_connected:
            self.iface.mapCanvas().scaleChanged.disconnect(self._on_map_refresh)
            self._scale_change_connected = False

    def _on_map_refresh(self):
        self._map_scale_timer.stop()
        self._map_scale_timer.start(1000)

    def _handle_scale_change_delayed(self):
        self._map_scale_timer.stop()
        if self._is_loading:
            self._map_scale_timer.start(750)
        if not self._is_loading and self._current_reader and self.connections_dialog.options.auto_zoom_enabled():
            new_scale = self._get_current_map_scale()
            has_scale_changed = self._current_scale is None or new_scale != self._current_scale
            if has_scale_changed:
                self._handle_scale_change(new_scale)

    def _handle_scale_change(self, new_scale):
        scale_increased = self._current_scale is None or new_scale > self._current_scale
        self._current_scale = new_scale
        max_zoom = self._current_reader.source.max_zoom()
        new_zoom = self._get_zoom_for_scale(new_scale)
        if new_zoom > max_zoom:
            new_zoom = max_zoom
        current_zoom = self._current_zoom
        if new_zoom != current_zoom or (scale_increased and new_scale > self._loaded_scale):
            if new_zoom != current_zoom:
                debug("Auto zoom: Reloading due to zoom level change from '{}' to '{}'", current_zoom, new_zoom)
            else:
                debug("Auto zoom: Reloading due to scale change from '{}' to '{}'", self._loaded_scale, new_scale)
            self._loaded_scale = new_scale
            self._reload_tiles()
            self.iface.mapCanvas().zoomScale(new_scale)

    def _handle_mouse_move(self, pos):
        self.iface.mapCanvas().xyCoordinates.disconnect(self._handle_mouse_move)
        zoom = self._get_current_zoom()
        lat_lon = epsg3857_to_wgs84_lonlat(pos[1], pos[0])
        tile = latlon_to_tile(zoom, lat_lon[0], lat_lon[1])
        msg = "XYZ-Position: {}, {}".format(tile[0], tile[1])
        self.iface.mainWindow().statusBar().showMessage(msg)
        self.iface.mapCanvas().xyCoordinates.connect(self._handle_mouse_move)

    def _add_path_to_icons(self):
        icons_directory = FileHelper.get_icons_directory()
        # current_paths = QgsApplication.instance().svgPaths()
        # if icons_directory not in current_paths:
        #     current_paths.append(icons_directory)
        #     QgsApplication.instance().setDefaultSvgPaths(current_paths)

    def _update_nr_of_tiles(self):
        zoom = self._get_current_zoom()
        bounds = self._get_visible_extent_as_tile_bounds(scheme="xyz", zoom=zoom)
        nr_of_tiles = bounds["width"] * bounds["height"]
        self.connections_dialog.set_nr_of_tiles(nr_of_tiles)

    def _show_connections_dialog(self):
        self._update_nr_of_tiles()
        self.connections_dialog.show()

    def _export_tiles(self):
        from vt_writer import VtWriter
        file_name = QFileDialog.getSaveFileName(None, "Export Vector Tiles", FileHelper.get_home_directory(), "mbtiles (*.mbtiles)")
        if file_name:
            self.export_action.setDisabled(True)
            try:
                self._current_writer = VtWriter(self.iface, file_name, progress_handler=self.handle_progress_update)
                self._create_progress_dialog(self.iface.mainWindow(), on_cancel=self._cancel_export)
                self._current_writer.export()
            except:
                critical("Error during export: {}", sys.exc_info())
            self.export_action.setEnabled(True)

    def _get_all_own_layers(self):
        layers = []
        for l in QgsMapLayerRegistry.instance().mapLayers().values():
            data_url = l.dataUrl().lower()
            if data_url and self._current_reader.source.source().lower().startswith(data_url):
                layers.append(l)
        return layers

    def _reload_tiles(self):
        if self._current_reader:
            self._create_progress_dialog(self.iface.mainWindow(), on_cancel=self._cancel_load)
            scheme = self._current_reader.source.scheme()
            zoom = self._get_current_zoom()
            auto_zoom_enabled = self.connections_dialog.options.auto_zoom_enabled()
            flush_loaded_layers = auto_zoom_enabled and zoom != self._current_zoom
            self._current_zoom = zoom
            if flush_loaded_layers:
                layers_to_remove = map(lambda layer: layer.id(), self._get_all_own_layers())
                debug("Flushing layers: {}", layers_to_remove)
                QgsMapLayerRegistry.instance().removeMapLayers(layers_to_remove)

            bounds = self._get_visible_extent_as_tile_bounds(scheme=scheme, zoom=zoom)
            if self.connections_dialog.options.auto_zoom_enabled():
                self._current_reader.always_overwrite_geojson(True)
            self._load_tiles(path=self._current_reader.source.source(),
                             options=self.connections_dialog.options,
                             layers_to_load=self._current_layer_filter,
                             bounds=bounds,
                             ignore_limit=True)

    def _get_visible_extent_as_tile_bounds(self, scheme, zoom):
        e = self.iface.mapCanvas().extent().asWktCoordinates().split(", ")
        new_extent = map(lambda x: map(float, x.split(" ")), e)
        min_extent = new_extent[0]
        max_extent = new_extent[1]

        min_proj = epsg3857_to_wgs84_lonlat(min_extent[0], min_extent[1])
        max_proj = epsg3857_to_wgs84_lonlat(max_extent[0], max_extent[1])

        bounds = []
        bounds.extend(min_proj)
        bounds.extend(max_proj)
        tile_bounds = get_tile_bounds(zoom, bounds=bounds, scheme=scheme, source_crs="EPSG:4326")

        debug("Current extent: {}", tile_bounds)
        return tile_bounds

    def _on_connect(self, connection_name, path_or_url):
        debug("Connect to path_or_url: {}", path_or_url)

        self.reload_action.setText("{} ({})".format(self._reload_button_text, connection_name))

        try:
            if self._current_reader:
                self._current_reader.source.close_connection()
            reader = self._create_reader(path_or_url)
            self._current_reader = reader
            if reader:
                layers = reader.source.vector_layers()
                self.connections_dialog.set_layers(layers)
                self.connections_dialog.options.set_zoom(reader.source.min_zoom(), reader.source.max_zoom())
                self.reload_action.setEnabled(True)
            else:
                self.connections_dialog.set_layers([])
                self.reload_action.setEnabled(False)
                self.reload_action.setText(self._reload_button_text)
        except:
            QMessageBox.critical(None, "Unexpected Error", "An unexpected error occured. {}".format(str(sys.exc_info()[1])))

    def show_about(self):
        AboutDialog().show()

    def _is_valid_qgis_extent(self, extent_to_load, zoom):
        source_bounds = self._current_reader.source.bounds_tile(zoom)
        if not source_bounds["x_min"] <= extent_to_load["x_min"] <= source_bounds["x_max"] \
                and not source_bounds["x_min"] <= extent_to_load["x_max"] <= source_bounds["x_max"] \
                and not source_bounds["y_min"] <= extent_to_load["y_min"] <= source_bounds["y_min"] \
                and not source_bounds["y_min"] <= extent_to_load["y_max"] <= source_bounds["y_min"]:
                return False
        return True

    def is_extent_within_bounds(self, extent, bounds):
        is_within = True
        if bounds:
            x_min_within = extent['x_min'] >= bounds['x_min']
            y_min_within = extent['y_min'] >= bounds['y_min']
            x_max_within = extent['x_max'] <= bounds['x_max']
            y_max_within = extent['y_max'] <= bounds['y_max']
            is_within = x_min_within and y_min_within and x_max_within and y_max_within
        else:
            debug("Bounds not available on source. Assuming extent is within bounds")
        return is_within

    def _on_add_layer(self, path_or_url, selected_layers):
        debug("add layer: {}", path_or_url)

        crs_string = self._current_reader.source.crs()
        self._init_qgis_map(crs_string)

        scheme = self._current_reader.source.scheme()
        zoom = self._get_current_zoom()

        extent = self._get_visible_extent_as_tile_bounds(scheme=scheme, zoom=zoom)

        bounds = self._current_reader.source.bounds_tile(zoom)
        info("Bounds of source: {}", bounds)
        is_within_bounds = self.is_extent_within_bounds(extent, bounds)
        if not is_within_bounds:
            # todo: set the current QGIS map extent inside the available bounds of the source
            pass

        if not self._is_valid_qgis_extent(extent_to_load=extent, zoom=zoom):
            extent = self._current_reader.source.bounds_tile(zoom)

        keep_dialog_open = self.connections_dialog.keep_dialog_open()
        if keep_dialog_open:
            dialog_owner = self.connections_dialog
        else:
            dialog_owner = self.iface.mainWindow()
            self.connections_dialog.close()
        self._create_progress_dialog(dialog_owner, on_cancel=self._cancel_load)
        self._load_tiles(path=path_or_url,
                         options=self.connections_dialog.options,
                         layers_to_load=selected_layers,
                         bounds=extent)
        self._current_layer_filter = selected_layers

    def _get_current_zoom(self):
        zoom = 14
        if self._current_reader:
            zoom = self._current_reader.source.max_zoom()
        if zoom is None:
            zoom = 14
        manual_zoom = self.connections_dialog.options.manual_zoom()
        if manual_zoom is not None:
            zoom = manual_zoom
        if self.connections_dialog.options.auto_zoom_enabled():
            scale_based_zoom = self._get_zoom_for_current_map_scale()
            if scale_based_zoom > zoom:
                scale_based_zoom = zoom
            zoom = scale_based_zoom
        return zoom

    def _set_qgis_extent(self, zoom, scheme, bounds):
        """
         * Sets the current extent of the QGIS map canvas to the specified bounds
        :return: 
        """
        min_pos = tile_to_latlon(zoom, bounds["x_min"], bounds["y_min"], scheme=scheme)
        max_pos = tile_to_latlon(zoom, bounds["x_max"], bounds["y_max"], scheme=scheme)
        map_min_pos = QgsPoint(min_pos[0], min_pos[1])
        map_max_pos = QgsPoint(max_pos[0], max_pos[1])
        rect = QgsRectangle(map_min_pos, map_max_pos)
        self.iface.mapCanvas().setExtent(rect)
        self.iface.mapCanvas().refresh()

    def _init_qgis_map(self, crs_string):
        crs = QgsCoordinateReferenceSystem(crs_string)
        if not crs.isValid():
            crs = QgsCoordinateReferenceSystem("EPSG:3857")
        self.iface.mapCanvas().mapRenderer().setDestinationCrs(crs)

    def _create_progress_dialog(self, owner, on_cancel):
        self.progress_dialog = ProgressDialog(owner)
        if on_cancel:
            self.progress_dialog.on_cancel.connect(on_cancel)

    def _cancel_load(self):
        if self._current_reader:
            self._current_reader.cancel()

    def _cancel_export(self):
        if self._current_writer:
            self._current_writer.cancel()

    def _create_action(self, title, icon, callback, is_enabled=True):
        new_action = QAction(QIcon(':/plugins/vector_tiles_reader/{}'.format(icon)), title, self.iface.mainWindow())
        new_action.triggered.connect(callback)
        new_action.setEnabled(is_enabled)
        return new_action

    def _load_tiles(self, path, options, layers_to_load, bounds=None, ignore_limit=False):
        self._is_loading = True
        merge_tiles = options.merge_tiles_enabled()
        apply_styles = options.apply_styles_enabled()
        tile_limit = options.tile_number_limit()
        load_mask_layer = options.load_mask_layer_enabled()
        auto_zoom = options.auto_zoom_enabled()
        if ignore_limit:
            tile_limit = None
        manual_zoom = options.manual_zoom()
        cartographic_ordering = options.cartographic_ordering()
        clip_tiles = options.clip_tiles()

        if apply_styles:
            self._set_background_color()

        debug("Load: {}", path)
        reader = self._current_reader
        if reader:
            reader.enable_cartographic_ordering(enabled=cartographic_ordering)
            try:
                max_zoom = reader.source.max_zoom()
                if auto_zoom:
                    zoom = self._get_zoom_for_current_map_scale()
                    if zoom > max_zoom:
                        zoom = max_zoom
                else:
                    zoom = max_zoom
                    if manual_zoom is not None:
                        zoom = manual_zoom
                self._current_zoom = zoom
                loaded_extent = reader.load_tiles(zoom_level=zoom,
                                                  layer_filter=layers_to_load,
                                                  load_mask_layer=load_mask_layer,
                                                  merge_tiles=merge_tiles,
                                                  clip_tiles=clip_tiles,
                                                  apply_styles=apply_styles,
                                                  max_tiles=tile_limit,
                                                  bounds=bounds,
                                                  limit_reacher_handler=lambda: self._show_limit_exceeded_message(
                                                      tile_limit))
                if self._current_scale is None:
                    self._current_scale = self._get_current_map_scale()
                self.refresh_layers()
                debug("Loading complete! Loaded extent: {}", loaded_extent)
                if loaded_extent and (not auto_zoom or (auto_zoom and self._loaded_scale is None)):
                    loaded_extent_is_within_bounds = (bounds["x_min"] <= loaded_extent["x_min"] <= bounds["x_max"] or \
                                                     bounds["x_min"] <= loaded_extent["x_max"] <= bounds["x_max"]) and \
                                                     (bounds["y_min"] <= loaded_extent["y_min"] <= bounds["y_max"] or \
                                                     bounds["y_min"] <= loaded_extent["y_max"] <= bounds["y_max"])
                    if not loaded_extent_is_within_bounds:
                        debug("Loaded extent is not within bounds")
                        self._set_qgis_extent(zoom=zoom, scheme=reader.source.scheme(), bounds=loaded_extent)
                if auto_zoom and not self._scale_change_connected:
                    self._connect_map_refresh()
            except Exception as e:
                traceback.print_exc()
                critical("An exception occured: {}", e)
                tb_lines = traceback.format_tb(sys.exc_traceback)
                tb_text = ""
                for line in tb_lines:
                    tb_text += line
                critical("{}", tb_text)
                self.iface.messageBar().pushMessage(
                    "Something went horribly wrong. Please have a look at the log.",
                    level=QgsMessageBar.CRITICAL,
                    duration=5)
                if self.progress_dialog:
                    self.progress_dialog.hide()
        self._is_loading = False

    def _set_background_color(self):
        myColor = QColor("#F2EFE9")
        # Write it to the project (will still need to be saved!)
        QgsProject.instance().writeEntry("Gui", "/CanvasColorRedPart", myColor.red())
        QgsProject.instance().writeEntry("Gui", "/CanvasColorGreenPart", myColor.green())
        QgsProject.instance().writeEntry("Gui", "/CanvasColorBluePart", myColor.blue())
        # And apply for the current session
        self.iface.mapCanvas().setCanvasColor(myColor)
        self.iface.mapCanvas().refresh()

    def refresh_layers(self):
        for layer in self.iface.mapCanvas().layers():
            layer.triggerRepaint()

    def _show_limit_exceeded_message(self, limit):
        """
        * Shows a message in QGIS that the nr of tiles has been restricted by the tile limit set in the options
        :return: 
        """
        if limit:
            self.iface.messageBar().pushMessage(
                "Only {} tiles were loaded according to the limit in the options".format(limit),
                level=QgsMessageBar.WARNING,
                duration=5)

    def _create_reader(self, path_or_url):
        # A lazy import is required because the vtreader depends on the external libs
        from vt_reader import VtReader
        reader = None
        try:
            reader = VtReader(self.iface,
                              path_or_url=path_or_url,
                              progress_handler=self.handle_progress_update)
        except RuntimeError:
            QMessageBox.critical(None, "Loading Error", str(sys.exc_info()[1]))
            critical(str(sys.exc_info()[1]))
        return reader

    def handle_progress_update(self, title, progress, max_progress, msg, show_progress):
        if show_progress:
            self.progress_dialog.open()
        elif show_progress is False:
            self.progress_dialog.hide()
            self.progress_dialog.set_message(None)
        if title:
            self.progress_dialog.setWindowTitle(title)
        if max_progress:
            self.progress_dialog.set_maximum(max_progress)
        if msg:
            self.progress_dialog.set_message(msg)
        if progress:
            self.progress_dialog.set_progress(progress)

    def _add_path_to_dependencies_to_syspath(self):
        """
         * Adds the path to the external libraries to the sys.path if not already added
        """
        ext_libs_path = os.path.abspath(os.path.dirname(__file__) + '/ext-libs')
        if ext_libs_path not in sys.path:
            site.addsitedir(ext_libs_path)

    def unload(self):
        if self._current_reader:
            self._current_reader.source.close_connection()
            self._current_reader = None
        try:
            self._disconnect_map_refresh()
        except:
            pass

        self.iface.layerToolBar().removeAction(self.toolButtonAction)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.about_action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.open_connections_action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.reload_action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.export_action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.clear_cache_action)
        self.iface.addLayerMenu().removeAction(self.open_connections_action)
        try:
            self.iface.mapCanvas().xyCoordinates.disconnect(self._handle_mouse_move)
        except:
            pass
