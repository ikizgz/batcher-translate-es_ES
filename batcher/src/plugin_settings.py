"""Plug-in settings."""

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

import pygimplib as pg

from src import actions as actions_
from src import builtin_constraints
from src import builtin_procedures
# Despite being unused, `setting_classes` must be imported so that the
# setting and GUI classes defined there are properly registered (via respective
# metaclasses in `pg.setting.meta`).
# noinspection PyUnresolvedReferences
from src import setting_classes
from src import utils


def create_settings_for_convert():
  settings = pg.setting.create_groups({
    'name': 'all_settings',
    'groups': [
      {
        'name': 'main',
      }
    ]
  })

  settings['main'].add([
    {
      'type': 'enum',
      'name': 'run_mode',
      'enum_type': Gimp.RunMode,
      'default_value': Gimp.RunMode.NONINTERACTIVE,
      'display_name': _('Run mode'),
      'description': _('The run mode'),
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'file',
      'name': 'inputs',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'none_ok': True,
      'display_name': _(
        'Text file containing input files and folders on each line'
        ' (non-interactive run mode only)'),
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'int',
      'name': 'max_num_inputs',
      'default_value': 2000,
      'min_value': 0,
      'display_name': _(
        'Maximum number of input files to process'
        ' (set to 0 to remove this restriction; non-interactive run mode only)'),
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'file_extension',
      'name': 'file_extension',
      'default_value': 'png',
      'display_name': _('File extension'),
      'adjust_value': True,
      'auto_update_gui_to_setting': False,
      'gui_type': None,
    },
    {
      'type': 'file',
      'name': 'output_directory',
      'default_value': Gio.file_new_for_path(pg.utils.get_default_dirpath()),
      'action': Gimp.FileChooserAction.SELECT_FOLDER,
      'display_name': _('Output folder'),
    },
    {
      'type': 'name_pattern',
      'name': 'name_pattern',
      'default_value': '[image name]',
      'display_name': _('Image filename pattern'),
      'description': _('Image filename pattern (empty string = image name)'),
      'gui_type': None,
    },
    {
      'type': 'choice',
      'name': 'overwrite_mode',
      'default_value': 'rename_new',
      'items': utils.semi_deep_copy(builtin_procedures.INTERACTIVE_OVERWRITE_MODES_LIST),
      'display_name': _('How to handle conflicting files (non-interactive run mode only)'),
      'gui_type': None,
    },
    {
      'type': 'file',
      'name': 'settings_file',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'none_ok': True,
      'display_name': _('File with saved settings'),
      'description': _('File with saved settings (optional)'),
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'string',
      'name': 'plugin_version',
      'default_value': pg.config.PLUGIN_VERSION,
      'pdb_type': None,
      'gui_type': None,
    },
  ])

  export_settings = pg.setting.Group(
    name='export',
    setting_attributes={
      'pdb_type': None,
    },
  )

  export_arguments = utils.semi_deep_copy(
    builtin_procedures.BUILTIN_PROCEDURES['export_for_convert']['arguments'])
  # Remove settings already present in the main settings.
  export_arguments = export_arguments[2:]

  export_settings.add(export_arguments)

  settings['main'].add([export_settings])

  gui_settings = _create_gui_settings('image_file_tree_items')
  gui_settings.add([
    _create_inputs_interactive_setting_dict(),
    _create_show_original_item_names_setting_dict(False),
    _create_keep_inputs_setting_dict(True, _('Keep Input Images')),
    _create_auto_close_setting_dict(False),
  ])

  size_gui_settings = pg.setting.Group(name='size')
  size_gui_settings.add(
    _create_size_gui_settings(
      dialog_position=(),
      dialog_size=(640, 640),
      paned_outside_previews_position=330,
      paned_between_previews_position=300,
    )
  )

  gui_settings.add([size_gui_settings])

  settings.add([gui_settings])

  remove_folder_structure_procedure_dict = utils.semi_deep_copy(
    builtin_procedures.BUILTIN_PROCEDURES['remove_folder_structure'])
  remove_folder_structure_procedure_dict['enabled'] = False
  remove_folder_structure_procedure_dict['display_options_on_create'] = False

  scale_procedure_dict = utils.semi_deep_copy(
    builtin_procedures.BUILTIN_PROCEDURES['scale_for_images'])
  scale_procedure_dict['enabled'] = False
  scale_procedure_dict['display_options_on_create'] = False

  settings['main'].add([
    actions_.create(
      name='procedures',
      initial_actions=[
        remove_folder_structure_procedure_dict,
        scale_procedure_dict,
      ]),
  ])

  settings['main'].add([
    actions_.create(
      name='constraints',
      initial_actions=[
        builtin_constraints.BUILTIN_CONSTRAINTS['recognized_file_format']]),
  ])

  builtin_procedures.set_sensitive_for_image_name_pattern_in_export_for_default_export_procedure(
    settings['main'])
  builtin_procedures.set_file_extension_options_for_default_export_procedure(settings['main'])

  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_crop_procedure)
  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_export_procedure)
  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_rotate_and_flip_procedure)
  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_scale_procedure)

  return settings


def create_settings_for_export_images():
  settings = pg.setting.create_groups({
    'name': 'all_settings',
    'groups': [
      {
        'name': 'main',
      }
    ]
  })

  settings['main'].add([
    {
      'type': 'enum',
      'name': 'run_mode',
      'enum_type': Gimp.RunMode,
      'default_value': Gimp.RunMode.NONINTERACTIVE,
      'display_name': _('Run mode'),
      'description': _('The run mode'),
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'file_extension',
      'name': 'file_extension',
      'default_value': 'png',
      'display_name': _('File extension'),
      'adjust_value': True,
      'auto_update_gui_to_setting': False,
      'gui_type': None,
    },
    {
      'type': 'file',
      'name': 'output_directory',
      'default_value': Gio.file_new_for_path(pg.utils.get_default_dirpath()),
      'action': Gimp.FileChooserAction.SELECT_FOLDER,
      'display_name': _('Output folder'),
    },
    {
      'type': 'name_pattern',
      'name': 'name_pattern',
      'default_value': '[image name]',
      'display_name': _('Image filename pattern'),
      'description': _('Image filename pattern (empty string = image name)'),
      'gui_type': None,
    },
    {
      'type': 'choice',
      'name': 'overwrite_mode',
      'default_value': 'rename_new',
      'items': utils.semi_deep_copy(builtin_procedures.INTERACTIVE_OVERWRITE_MODES_LIST),
      'display_name': _('How to handle conflicting files (non-interactive run mode only)'),
      'gui_type': None,
    },
    {
      'type': 'file',
      'name': 'settings_file',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'none_ok': True,
      'display_name': _('File with saved settings'),
      'description': _('File with saved settings (optional)'),
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'string',
      'name': 'plugin_version',
      'default_value': pg.config.PLUGIN_VERSION,
      'pdb_type': None,
      'gui_type': None,
    },
  ])

  export_settings = pg.setting.Group(
    name='export',
    setting_attributes={
      'pdb_type': None,
    },
  )

  export_arguments = utils.semi_deep_copy(
    builtin_procedures.BUILTIN_PROCEDURES['export_for_export_images']['arguments'])
  # Remove settings already present in the main settings.
  export_arguments = export_arguments[2:]

  export_settings.add(export_arguments)

  settings['main'].add([export_settings])

  gui_settings = _create_gui_settings('gimp_image_tree_items')
  gui_settings.add([
    _create_auto_close_setting_dict(True),
    _create_show_quick_settings_setting_dict(),
  ])

  size_gui_settings = pg.setting.Group(name='size')
  size_gui_settings.add(
    _create_size_gui_settings(
      dialog_position=(),
      dialog_size=(640, 540),
      paned_outside_previews_position=330,
      paned_between_previews_position=225,
    )
  )

  gui_settings.add([size_gui_settings])

  settings.add([gui_settings])

  scale_procedure_dict = utils.semi_deep_copy(
    builtin_procedures.BUILTIN_PROCEDURES['scale_for_images'])
  scale_procedure_dict['enabled'] = False
  scale_procedure_dict['display_options_on_create'] = False

  settings['main'].add([
    actions_.create(
      name='procedures',
      initial_actions=[
        scale_procedure_dict,
      ]),
  ])

  not_saved_or_exported_constraint_dict = utils.semi_deep_copy(
    builtin_constraints.BUILTIN_CONSTRAINTS['not_saved_or_exported'])
  not_saved_or_exported_constraint_dict['enabled'] = False

  with_unsaved_changes_constraint_dict = utils.semi_deep_copy(
    builtin_constraints.BUILTIN_CONSTRAINTS['with_unsaved_changes'])
  with_unsaved_changes_constraint_dict['enabled'] = False

  settings['main'].add([
    actions_.create(
      name='constraints',
      initial_actions=[
        not_saved_or_exported_constraint_dict,
        with_unsaved_changes_constraint_dict,
      ]),
  ])

  builtin_procedures.set_sensitive_for_image_name_pattern_in_export_for_default_export_procedure(
    settings['main'])
  builtin_procedures.set_file_extension_options_for_default_export_procedure(settings['main'])

  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_crop_procedure)
  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_export_procedure)
  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_rotate_and_flip_procedure)
  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_scale_procedure)

  return settings


def create_settings_for_export_layers():
  settings = pg.setting.create_groups({
    'name': 'all_settings',
    'groups': [
      {
        'name': 'main',
      }
    ]
  })
  
  settings['main'].add([
    {
      'type': 'file_extension',
      'name': 'file_extension',
      'default_value': 'png',
      'display_name': _('File extension'),
      'adjust_value': True,
      'auto_update_gui_to_setting': False,
      'gui_type': None,
    },
    {
      'type': 'file',
      'name': 'output_directory',
      'default_value': Gio.file_new_for_path(pg.utils.get_default_dirpath()),
      'action': Gimp.FileChooserAction.SELECT_FOLDER,
      'display_name': _('Output folder'),
    },
    {
      'type': 'name_pattern',
      'name': 'name_pattern',
      'default_value': '[layer name]',
      'display_name': _('Layer filename pattern'),
      'description': _('Layer filename pattern (empty string = layer name)'),
      'gui_type': None,
    },
    {
      'type': 'choice',
      'name': 'overwrite_mode',
      'default_value': 'rename_new',
      'items': utils.semi_deep_copy(builtin_procedures.INTERACTIVE_OVERWRITE_MODES_LIST),
      'display_name': _('How to handle conflicting files (non-interactive run mode only)'),
      'gui_type': None,
    },
    {
      'type': 'file',
      'name': 'settings_file',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'none_ok': True,
      'display_name': _('File with saved settings'),
      'description': _('File with saved settings (optional)'),
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'tagged_items',
      'name': 'tagged_items',
      'default_value': [],
      'pdb_type': None,
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'string',
      'name': 'plugin_version',
      'default_value': pg.config.PLUGIN_VERSION,
      'pdb_type': None,
      'gui_type': None,
    },
  ])

  export_settings = pg.setting.Group(
    name='export',
    setting_attributes={
      'pdb_type': None,
    },
  )

  export_arguments = utils.semi_deep_copy(
    builtin_procedures.BUILTIN_PROCEDURES['export_for_export_layers']['arguments'])
  # Remove settings already present in the main settings.
  export_arguments = export_arguments[2:]

  export_settings.add(export_arguments)

  settings['main'].add([export_settings])

  gui_settings = _create_gui_settings('gimp_item_tree_items')
  gui_settings.add([
    _create_auto_close_setting_dict(True),
    _create_show_quick_settings_setting_dict(),
    _create_images_and_directories_setting_dict(),
  ])

  size_gui_settings = pg.setting.Group(name='size')
  size_gui_settings.add(
    _create_size_gui_settings(
      dialog_position=(),
      dialog_size=(640, 540),
      paned_outside_previews_position=330,
      paned_between_previews_position=225,
    )
  )

  gui_settings.add([size_gui_settings])

  settings.add([gui_settings])

  settings['main'].add([
    actions_.create(
      name='procedures',
      initial_actions=[builtin_procedures.BUILTIN_PROCEDURES['resize_to_layer_size']]),
  ])

  visible_constraint_dict = utils.semi_deep_copy(builtin_constraints.BUILTIN_CONSTRAINTS['visible'])
  visible_constraint_dict['enabled'] = False
  
  settings['main'].add([
    actions_.create(
      name='constraints',
      initial_actions=[
        builtin_constraints.BUILTIN_CONSTRAINTS['layers'],
        visible_constraint_dict]),
  ])

  builtin_procedures.set_sensitive_for_image_name_pattern_in_export_for_default_export_procedure(
    settings['main'])
  builtin_procedures.set_file_extension_options_for_default_export_procedure(settings['main'])

  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_crop_procedure)
  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_export_procedure)
  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_rotate_and_flip_procedure)
  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_scale_procedure)

  settings['main/procedures'].connect_event(
    'after-add-action',
    builtin_procedures.on_after_add_insert_background_foreground_for_layers,
    settings['main/tagged_items'],
  )

  return settings


def create_settings_for_edit_layers():
  settings = pg.setting.create_groups({
    'name': 'all_settings',
    'groups': [
      {
        'name': 'main',
      }
    ]
  })

  settings['main'].add([
    {
      'type': 'file',
      'name': 'settings_file',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'none_ok': True,
      'display_name': _('File with saved settings'),
      'description': _('File with saved settings (optional)'),
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'tagged_items',
      'name': 'tagged_items',
      'default_value': [],
      'pdb_type': None,
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'string',
      'name': 'plugin_version',
      'default_value': pg.config.PLUGIN_VERSION,
      'pdb_type': None,
      'gui_type': None,
    },
  ])

  gui_settings = _create_gui_settings('gimp_item_tree_items')
  gui_settings.add([_create_auto_close_setting_dict(False)])

  size_gui_settings = pg.setting.Group(name='size')
  size_gui_settings.add(
    _create_size_gui_settings(
      dialog_position=(),
      dialog_size=(570, 500),
      paned_outside_previews_position=300,
      paned_between_previews_position=220,
    )
  )

  gui_settings.add([size_gui_settings])

  settings.add([gui_settings])

  rename_procedure_dict = utils.semi_deep_copy(
    builtin_procedures.BUILTIN_PROCEDURES['rename_for_edit_layers'])
  rename_procedure_dict['enabled'] = False
  rename_procedure_dict['display_options_on_create'] = False
  rename_procedure_dict['arguments'][0]['default_value'] = 'image[001]'

  settings['main'].add([
    actions_.create(
      name='procedures',
      initial_actions=[rename_procedure_dict]),
  ])

  visible_constraint_dict = utils.semi_deep_copy(builtin_constraints.BUILTIN_CONSTRAINTS['visible'])
  visible_constraint_dict['enabled'] = False

  selected_in_gimp_constraint_dict = utils.semi_deep_copy(
    builtin_constraints.BUILTIN_CONSTRAINTS['selected_in_gimp'])
  selected_in_gimp_constraint_dict['enabled'] = False

  settings['main'].add([
    actions_.create(
      name='constraints',
      initial_actions=[
        builtin_constraints.BUILTIN_CONSTRAINTS['layers'],
        visible_constraint_dict,
        selected_in_gimp_constraint_dict,
      ]),
  ])

  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_crop_procedure)
  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_export_procedure)
  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_rotate_and_flip_procedure)
  settings['main/procedures'].connect_event(
    'after-add-action', builtin_procedures.on_after_add_scale_procedure)

  settings['main/procedures'].connect_event(
    'after-add-action',
    builtin_procedures.on_after_add_insert_background_foreground_for_layers,
    settings['main/tagged_items'],
  )

  return settings


def _create_gui_settings(item_tree_items_setting_type):
  gui_settings = pg.setting.Group(name='gui')

  procedure_browser_settings = pg.setting.Group(name='procedure_browser')

  procedure_browser_settings.add([
    {
      'type': 'integer',
      'name': 'paned_position',
      'default_value': 325,
      'gui_type': None,
    },
    {
      'type': 'tuple',
      'name': 'dialog_position',
      'default_value': (),
    },
    {
      'type': 'tuple',
      'name': 'dialog_size',
      'default_value': (800, 450),
    },
  ])

  gui_settings.add([
    {
      'type': 'bool',
      'name': 'name_preview_sensitive',
      'default_value': True,
      'gui_type': None,
    },
    {
      'type': 'bool',
      'name': 'image_preview_sensitive',
      'default_value': True,
      'gui_type': None,
    },
    {
      'type': 'bool',
      'name': 'image_preview_automatic_update',
      'default_value': True,
      'gui_type': None,
    },
    {
      'type': 'bool',
      'name': 'image_preview_automatic_update_if_below_maximum_duration',
      'default_value': True,
      'gui_type': None,
    },
    {
      'type': item_tree_items_setting_type,
      'name': 'selected_items',
    },
    {
      'type': item_tree_items_setting_type,
      'name': 'name_preview_items_collapsed_state',
    },
    {
      'type': item_tree_items_setting_type,
      'name': 'image_preview_displayed_items',
    },
    procedure_browser_settings,
  ])

  return gui_settings


def _create_size_gui_settings(
      dialog_position,
      dialog_size,
      paned_outside_previews_position,
      paned_between_previews_position,
):
  return [
    {
      'type': 'tuple',
      'name': 'dialog_position',
      'default_value': dialog_position,
    },
    {
      'type': 'tuple',
      'name': 'dialog_size',
      'default_value': dialog_size,
    },
    {
      'type': 'integer',
      'name': 'paned_outside_previews_position',
      'default_value': paned_outside_previews_position,
      'gui_type': None,
    },
    {
      'type': 'integer',
      'name': 'paned_between_previews_position',
      'default_value': paned_between_previews_position,
      'gui_type': None,
    },
  ]


def _create_inputs_interactive_setting_dict():
  return {
    'type': 'list',
    'name': 'inputs_interactive',
    'display_name': _('Input files and folders'),
    'pdb_type': None,
    'gui_type': None,
  }


def _create_show_original_item_names_setting_dict(default_value):
  return {
    'type': 'bool',
    'name': 'show_original_item_names',
    'default_value': default_value,
    'display_name': _('Show Original Names'),
  }


def _create_keep_inputs_setting_dict(default_value, title):
  return {
    'type': 'bool',
    'name': 'keep_inputs',
    'default_value': default_value,
    'display_name': title,
    'gui_type': 'check_menu_item',
  }


def _create_auto_close_setting_dict(default_value):
  return {
    'type': 'bool',
    'name': 'auto_close',
    'default_value': default_value,
    'display_name': _('Close when Done'),
    'gui_type': 'check_menu_item',
  }


def _create_show_quick_settings_setting_dict():
  return {
    'type': 'bool',
    'name': 'show_quick_settings',
    'default_value': True,
    'gui_type': None,
  }


def _create_images_and_directories_setting_dict():
  return {
    'type': 'images_and_directories',
    'name': 'images_and_directories',
  }
