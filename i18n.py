"""
i18n.py — Sentinel Internationalization Engine
===============================================
Comprehensive multilingual dictionary supporting:
  - pt_BR: Português (Brasil) — Primary Default
  - en_US: English
  - es_ES: Español

Provides instant runtime UI translation without requiring an application restart.
"""

from typing import Dict, Any

DEFAULT_LANGUAGE = "pt_BR"
_CURRENT_LANGUAGE = DEFAULT_LANGUAGE

LANGUAGES = {
    "pt_BR": "Português (Brasil)",
    "en_US": "English",
    "es_ES": "Español",
}

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "pt_BR": {
        # Window & General
        "app_title": "Sentinel — Monitoramento de Entrada e Saída",
        "ready_start": "Pronto. Clique em Iniciar para começar.",
        "camera_offline": "Câmera desconectada",
        "camera_stopped": "Câmera parada.",
        "camera_error": "Erro na câmera: {error}",
        "cannot_open_camera": "Não foi possível abrir a câmera {index}. Verifique a conexão.",
        "camera_online_ai": "Câmera conectada — Reconhecimento facial e emoções ativos.",
        "camera_online_no_ai": "Câmera conectada — Biblioteca face_recognition indisponível.",
        "opening_camera": "Abrindo câmera…",

        # Toolbar
        "start": "Iniciar",
        "stop": "Parar",
        "camera_label": "Câmera:",
        "tripwire_label": "Linha de Detecção:",
        "language_label": "Idioma:",
        "tripwire_tooltip": "Posição vertical da linha de entrada/saída (% da tela)",

        # Section titles
        "live_feed": "Transmissão ao Vivo",
        "event_log": "Registro de Eventos",
        "registered_users": "Pessoas Cadastradas",
        "register_section": "Cadastrar Pessoa:",

        # Event Log Table
        "col_time": "Horário",
        "col_thumb": "Foto",
        "col_name": "Nome",
        "col_direction": "Direção",
        "col_emotion": "Expressão",
        "btn_clear": "Limpar",
        "btn_export": "Exportar CSV",
        "clear_tooltip": "Limpar exibição da tabela (os dados continuam salvos no banco)",
        "no_image": "-",

        # Registered Users Table
        "col_role": "Função",
        "col_registered_at": "Data do Cadastro",
        "col_action": "",
        "btn_delete_tooltip": "Descadastrar {name}",
        "search_placeholder": "Filtrar por nome...",
        "user_count": "{count} pessoa(s) cadastrada(s)",

        # Registration Bar
        "name_label": "Nome:",
        "name_placeholder": "ex: Maria Silva",
        "role_label": "Função:",
        "btn_capture": "Capturar Rosto",
        "btn_capture_tooltip": "Congela o próximo quadro e analisa os traços faciais",
        "btn_save": "Salvar Pessoa",
        "btn_save_tooltip": "Salva o perfil biométrico no banco de dados",
        "status_no_face_yet": "Nenhum rosto capturado ainda.",
        "status_capturing": "Capturando rosto...",
        "status_captured_success": "Rosto capturado com sucesso — clique em Salvar Pessoa.",
        "status_no_face_detected": "Nenhum rosto detectado. Aproxime-se e tente novamente.",
        "status_saved_success": "Pessoa cadastrada com sucesso.",

        # Roles
        "role_family": "Família",
        "role_guest": "Convidado",
        "role_delivery": "Entregador",
        "role_staff": "Funcionário",
        "role_other": "Outro",

        # Directions
        "dir_enter": "ENTROU",
        "dir_exit": "SAIU",

        # Emotions
        "emotion_neutral": "Neutro",
        "emotion_happy": "Feliz",
        "emotion_surprised": "Surpreso",
        "emotion_sad": "Triste",
        "emotion_angry": "Irritado",
        "emotion_disgusted": "Indignado",
        "emotion_fearful": "Apreensivo",
        "emotion_contempt": "Neutro",

        # Alerts and Modals
        "alert_cam_not_running_title": "Câmera Parada",
        "alert_cam_not_running_msg": "Inicie a câmera antes de tentar capturar um rosto.",
        "alert_name_required_title": "Nome Obrigatório",
        "alert_name_required_msg": "Por favor, digite um nome antes de capturar ou salvar.",
        "alert_no_face_title": "Nenhum Rosto Capturado",
        "alert_no_face_msg": "Capture um rosto com sucesso antes de salvar.",
        "confirm_unregister_title": "Confirmar Exclusão",
        "confirm_unregister_msg": "Deseja remover '{name}' do sistema?\nOs dados biométricos serão excluídos permanentemente.",
        "user_removed_status": "Pessoa '{name}' removida com sucesso.",
        "export_complete_title": "Exportação Concluída",
        "export_complete_msg": "Exportados {count} registros para:\n{path}",
        "csv_filter": "Arquivos CSV (*.csv)",
        "csv_default_name": "registros_sentinel",
        "error_saving_title": "Erro ao Salvar",
        "error_saving_msg": "Não foi possível cadastrar a pessoa: {error}",
        "error_deleting_title": "Erro ao Excluir",
        "error_deleting_msg": "Não foi possível excluir a pessoa: {error}",

        # HUD Overlay
        "hud_tripwire": "< LINHA DE DETECCAO >",
        "hud_unknown": "Desconhecido",
        "hud_face_captured": "Rosto Capturado!",
        "hud_no_face": "Nenhum rosto detectado - aproxime-se",

        # Menu Bar & Updates
        "menu_file": "Arquivo",
        "menu_help": "Ajuda",
        "menu_export_csv": "Exportar Registros...",
        "menu_exit": "Sair",
        "menu_check_updates": "Verificar Atualizações...",
        "menu_about": "Sobre o Sentinel",
        "about_title": "Sobre o Sentinel",
        "about_body": "Sentinel v{version}\nSistema de Monitoramento Facial de Entrada e Saída\nDesenvolvido com visão computacional de alta performance e aprendizado profundo.",
        "update_banner_text": "Nova versão do Sentinel ({version}) disponível!",
        "update_btn_update": "Atualizar Agora",
        "update_btn_dismiss": "Dispensar",
        "update_dialog_title": "Atualização do Sentinel",
        "update_available_title": "Nova Versão Disponível",
        "update_current_version": "Versão Atual: {version}",
        "update_new_version": "Nova Versão: {version}",
        "update_release_notes": "Notas da Versão:",
        "update_downloading": "Baixando atualização... {percent}% ({speed})",
        "update_download_complete": "Download concluído! Clique em Instalar e Reiniciar.",
        "update_install_restart": "Instalar e Reiniciar",
        "update_checking": "Verificando atualizações...",
        "update_up_to_date_title": "Sentinel Atualizado",
        "update_up_to_date_msg": "Você já está usando a versão mais recente do Sentinel (v{version}).",
        "update_error_title": "Erro na Atualização",
        "update_error_msg": "Não foi possível verificar atualizações:\n{error}",
        "update_cancel": "Cancelar",
    },

    "en_US": {
        # Window & General
        "app_title": "Sentinel — Home Entry/Exit Tracker",
        "ready_start": "Ready. Click Start to begin.",
        "camera_offline": "Camera offline",
        "camera_stopped": "Camera stopped.",
        "camera_error": "Camera error: {error}",
        "cannot_open_camera": "Cannot open camera {index}. Check connection.",
        "camera_online_ai": "Camera online — AI facial recognition and emotion active.",
        "camera_online_no_ai": "Camera online — face_recognition library not available.",
        "opening_camera": "Opening camera…",

        # Toolbar
        "start": "Start",
        "stop": "Stop",
        "camera_label": "Camera:",
        "tripwire_label": "Tripwire:",
        "language_label": "Language:",
        "tripwire_tooltip": "Vertical position of the entry/exit tripwire (% of frame)",

        # Section titles
        "live_feed": "Live Feed",
        "event_log": "Event Log",
        "registered_users": "Registered Users",
        "register_section": "Register Person:",

        # Event Log Table
        "col_time": "Time",
        "col_thumb": "Photo",
        "col_name": "Name",
        "col_direction": "Direction",
        "col_emotion": "Expression",
        "btn_clear": "Clear",
        "btn_export": "Export CSV",
        "clear_tooltip": "Clear the log display (does not delete DB records)",
        "no_image": "-",

        # Registered Users Table
        "col_role": "Role",
        "col_registered_at": "Registration Date",
        "col_action": "",
        "btn_delete_tooltip": "Unregister {name}",
        "search_placeholder": "Filter by name...",
        "user_count": "{count} registered user(s)",

        # Registration Bar
        "name_label": "Name:",
        "name_placeholder": "e.g. John Doe",
        "role_label": "Role:",
        "btn_capture": "Capture Face",
        "btn_capture_tooltip": "Freeze the next frame and extract face features",
        "btn_save": "Save Person",
        "btn_save_tooltip": "Save the biometric profile to the database",
        "status_no_face_yet": "No face captured yet.",
        "status_capturing": "Capturing face...",
        "status_captured_success": "Face captured — click Save Person.",
        "status_no_face_detected": "No face detected. Move closer and try again.",
        "status_saved_success": "Person saved successfully.",

        # Roles
        "role_family": "Family",
        "role_guest": "Guest",
        "role_delivery": "Delivery",
        "role_staff": "Staff",
        "role_other": "Other",

        # Directions
        "dir_enter": "ENTER",
        "dir_exit": "EXIT",

        # Emotions
        "emotion_neutral": "Neutral",
        "emotion_happy": "Happy",
        "emotion_surprised": "Surprised",
        "emotion_sad": "Sad",
        "emotion_angry": "Angry",
        "emotion_disgusted": "Disgusted",
        "emotion_fearful": "Fearful",
        "emotion_contempt": "Neutral",

        # Alerts and Modals
        "alert_cam_not_running_title": "Camera Not Running",
        "alert_cam_not_running_msg": "Please start the camera before capturing a face.",
        "alert_name_required_title": "Name Required",
        "alert_name_required_msg": "Please enter a name before capturing or saving.",
        "alert_no_face_title": "No Face Captured",
        "alert_no_face_msg": "Capture a face first before saving.",
        "confirm_unregister_title": "Confirm Unregister",
        "confirm_unregister_msg": "Remove '{name}' from the system?\nTheir biometric data will be permanently deleted.",
        "user_removed_status": "User '{name}' removed successfully.",
        "export_complete_title": "Export Complete",
        "export_complete_msg": "Exported {count} log entries to:\n{path}",
        "csv_filter": "CSV Files (*.csv)",
        "csv_default_name": "sentinel_log",
        "error_saving_title": "Error Saving Person",
        "error_saving_msg": "Could not save person: {error}",
        "error_deleting_title": "Error Deleting User",
        "error_deleting_msg": "Could not delete user: {error}",

        # HUD Overlay
        "hud_tripwire": "< TRIPWIRE >",
        "hud_unknown": "Unknown",
        "hud_face_captured": "Face Captured!",
        "hud_no_face": "No face detected - move closer",

        # Menu Bar & Updates
        "menu_file": "File",
        "menu_help": "Help",
        "menu_export_csv": "Export Event Log...",
        "menu_exit": "Exit",
        "menu_check_updates": "Check for Updates...",
        "menu_about": "About Sentinel",
        "about_title": "About Sentinel",
        "about_body": "Sentinel v{version}\nHome Entry/Exit Facial Monitoring System\nBuilt with high-performance computer vision and deep learning.",
        "update_banner_text": "A new version of Sentinel ({version}) is available!",
        "update_btn_update": "Update Now",
        "update_btn_dismiss": "Dismiss",
        "update_dialog_title": "Sentinel Software Update",
        "update_available_title": "New Version Available",
        "update_current_version": "Current Version: {version}",
        "update_new_version": "New Version: {version}",
        "update_release_notes": "Release Notes:",
        "update_downloading": "Downloading update... {percent}% ({speed})",
        "update_download_complete": "Download complete! Click Install & Restart.",
        "update_install_restart": "Install & Restart",
        "update_checking": "Checking for updates...",
        "update_up_to_date_title": "Sentinel is Up to Date",
        "update_up_to_date_msg": "You are running the latest version of Sentinel (v{version}).",
        "update_error_title": "Update Error",
        "update_error_msg": "Could not check for updates:\n{error}",
        "update_cancel": "Cancel",
    },

    "es_ES": {
        # Window & General
        "app_title": "Sentinel — Monitoreo de Entrada y Salida",
        "ready_start": "Listo. Haga clic en Iniciar para comenzar.",
        "camera_offline": "Cámara desconectada",
        "camera_stopped": "Cámara detenida.",
        "camera_error": "Error de cámara: {error}",
        "cannot_open_camera": "No se pudo abrir la cámara {index}. Compruebe la conexión.",
        "camera_online_ai": "Cámara conectada — Reconocimiento facial y emociones activos.",
        "camera_online_no_ai": "Cámara conectada — Librería face_recognition no disponible.",
        "opening_camera": "Abriendo cámara…",

        # Toolbar
        "start": "Iniciar",
        "stop": "Detener",
        "camera_label": "Cámara:",
        "tripwire_label": "Línea de Cruce:",
        "language_label": "Idioma:",
        "tripwire_tooltip": "Posición vertical de la línea de entrada/salida (% de pantalla)",

        # Section titles
        "live_feed": "Transmisión en Vivo",
        "event_log": "Registro de Eventos",
        "registered_users": "Personas Registradas",
        "register_section": "Registrar Persona:",

        # Event Log Table
        "col_time": "Hora",
        "col_thumb": "Foto",
        "col_name": "Nombre",
        "col_direction": "Dirección",
        "col_emotion": "Expresión",
        "btn_clear": "Limpiar",
        "btn_export": "Exportar CSV",
        "clear_tooltip": "Limpiar la tabla en pantalla (los datos se conservan en la base de datos)",
        "no_image": "-",

        # Registered Users Table
        "col_role": "Rol",
        "col_registered_at": "Fecha de Registro",
        "col_action": "",
        "btn_delete_tooltip": "Eliminar a {name}",
        "search_placeholder": "Filtrar por nombre...",
        "user_count": "{count} persona(s) registrada(s)",

        # Registration Bar
        "name_label": "Nombre:",
        "name_placeholder": "ej: Carlos Gómez",
        "role_label": "Rol:",
        "btn_capture": "Capturar Rostro",
        "btn_capture_tooltip": "Congela el cuadro y extrae las facciones del rostro",
        "btn_save": "Guardar Persona",
        "btn_save_tooltip": "Guarda el perfil biométrico en la base de datos",
        "status_no_face_yet": "Aún no se ha capturado ningún rostro.",
        "status_capturing": "Capturando rostro...",
        "status_captured_success": "Rostro capturado con éxito — haga clic en Guardar Persona.",
        "status_no_face_detected": "No se detectó ningún rostro. Acérquese e intente nuevamente.",
        "status_saved_success": "Persona guardada correctamente.",

        # Roles
        "role_family": "Familia",
        "role_guest": "Invitado",
        "role_delivery": "Repartidor",
        "role_staff": "Personal",
        "role_other": "Otro",

        # Directions
        "dir_enter": "ENTRÓ",
        "dir_exit": "SALIÓ",

        # Emotions
        "emotion_neutral": "Neutral",
        "emotion_happy": "Feliz",
        "emotion_surprised": "Sorprendido",
        "emotion_sad": "Triste",
        "emotion_angry": "Enojado",
        "emotion_disgusted": "Indignado",
        "emotion_fearful": "Temeroso",
        "emotion_contempt": "Neutral",

        # Alerts and Modals
        "alert_cam_not_running_title": "Cámara Detenida",
        "alert_cam_not_running_msg": "Inicie la cámara antes de capturar un rostro.",
        "alert_name_required_title": "Nombre Requerido",
        "alert_name_required_msg": "Por favor ingrese un nombre antes de capturar o guardar.",
        "alert_no_face_title": "Ningún Rostro Capturado",
        "alert_no_face_msg": "Capture un rostro antes de guardar.",
        "confirm_unregister_title": "Confirmar Eliminación",
        "confirm_unregister_msg": "¿Desea eliminar a '{name}' del sistema?\nLos datos biométricos se borrarán permanentemente.",
        "user_removed_status": "Persona '{name}' eliminada correctamente.",
        "export_complete_title": "Exportación Finalizada",
        "export_complete_msg": "Se exportaron {count} registros a:\n{path}",
        "csv_filter": "Archivos CSV (*.csv)",
        "csv_default_name": "registros_sentinel",
        "error_saving_title": "Error al Guardar",
        "error_saving_msg": "No se pudo guardar la persona: {error}",
        "error_deleting_title": "Error al Eliminar",
        "error_deleting_msg": "No se pudo eliminar la persona: {error}",

        # HUD Overlay
        "hud_tripwire": "< LINEA DE DETECCION >",
        "hud_unknown": "Desconocido",
        "hud_face_captured": "Rostro Capturado!",
        "hud_no_face": "No se detecta rostro - acerquese",

        # Menu Bar & Updates
        "menu_file": "Archivo",
        "menu_help": "Ayuda",
        "menu_export_csv": "Exportar Registros...",
        "menu_exit": "Salir",
        "menu_check_updates": "Buscar Actualizaciones...",
        "menu_about": "Acerca de Sentinel",
        "about_title": "Acerca de Sentinel",
        "about_body": "Sentinel v{version}\nSistema de Monitoreo Facial de Entrada y Salida\nDesarrollado con visión artificial de alto rendimiento y aprendizaje profundo.",
        "update_banner_text": "¡Nueva versión de Sentinel ({version}) disponible!",
        "update_btn_update": "Actualizar Ahora",
        "update_btn_dismiss": "Descartar",
        "update_dialog_title": "Actualización de Sentinel",
        "update_available_title": "Nueva Versión Disponible",
        "update_current_version": "Versión Actual: {version}",
        "update_new_version": "Nueva Versión: {version}",
        "update_release_notes": "Notas de la Versión:",
        "update_downloading": "Descargando actualización... {percent}% ({speed})",
        "update_download_complete": "¡Descarga completada! Haga clic en Instalar y Reiniciar.",
        "update_install_restart": "Instalar y Reiniciar",
        "update_checking": "Buscando actualizaciones...",
        "update_up_to_date_title": "Sentinel Actualizado",
        "update_up_to_date_msg": "Ya está utilizando la versión más reciente de Sentinel (v{version}).",
        "update_error_title": "Error de Actualización",
        "update_error_msg": "No se pudieron comprobar las actualizaciones:\n{error}",
        "update_cancel": "Cancelar",
    },
}


def set_language(lang_code: str) -> None:
    """Set the active language code (pt_BR, en_US, es_ES)."""
    global _CURRENT_LANGUAGE
    if lang_code in TRANSLATIONS:
        _CURRENT_LANGUAGE = lang_code
    else:
        _CURRENT_LANGUAGE = DEFAULT_LANGUAGE


def get_language() -> str:
    """Return the active language code."""
    return _CURRENT_LANGUAGE


def t(key: str, **kwargs: Any) -> str:
    """
    Translate a key into the active language, falling back to pt_BR and key string.
    Supports kwargs string interpolation.
    """
    dict_lang = TRANSLATIONS.get(_CURRENT_LANGUAGE, TRANSLATIONS[DEFAULT_LANGUAGE])
    val = dict_lang.get(key)
    if val is None:
        val = TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    if kwargs:
        try:
            return val.format(**kwargs)
        except Exception:
            return val
    return val


def translate_direction(direction: str) -> str:
    """Convert ENTER/EXIT into localized label."""
    if direction == "ENTER":
        return t("dir_enter")
    elif direction == "EXIT":
        return t("dir_exit")
    return direction


def translate_emotion(emotion: str) -> str:
    """Translate raw emotion class (Happy, Sad, Neutral...) into localized string."""
    key = f"emotion_{emotion.lower()}"
    return t(key)


def get_roles_list() -> list:
    """Return list of standard roles localized in the active language."""
    return [
        t("role_family"),
        t("role_guest"),
        t("role_delivery"),
        t("role_staff"),
        t("role_other"),
    ]
