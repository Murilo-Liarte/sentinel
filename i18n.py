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

        # Settings Menu & Dialog
        "menu_settings": "Configurações",
        "menu_open_settings": "Abrir Configurações...",
        "menu_fps_settings": "Taxa de Quadros (FPS)...",
        "menu_lang_settings": "Idioma da Interface...",
        "settings_dialog_title": "Configurações do Sentinel",
        "settings_tab_general": "Geral",
        "settings_tab_camera": "Câmera e Desempenho",
        "settings_lang_label": "Idioma da Interface:",
        "settings_lang_desc": "Altere o idioma do aplicativo instantaneamente.",
        "settings_fps_label": "Taxa de Quadros da Câmera (FPS):",
        "settings_fps_desc": "Limite de FPS da captura. 30 FPS é recomendado. Reduza para 15 ou 20 FPS em máquinas com menor poder de processamento.",
        "settings_version_label": "Versão Instalada:",
        "settings_version_info": "Sentinel v{version} (Compilação Nativa x64)",
        "settings_engine_info": "Motor: dlib C++ & PySide6 & Busca Vetorial BLAS",
        "settings_btn_check_update": "Verificar Atualizações",
        "settings_btn_save": "Salvar e Fechar",

        # Theme
        "settings_theme_label": "Aparência e Tema:",
        "settings_theme_desc": "Alterne entre o Modo Escuro e o Modo Claro (Dia).",
        "theme_dark": "Modo Escuro (Padrão)",
        "theme_light": "Modo Claro (Dia)",

        # Camera Input
        "settings_cam_label": "Dispositivo de Câmera:",
        "settings_cam_desc": "Selecione o sensor de vídeo ou webcam a ser utilizado.",
        "cam_device_0": "Câmera 0 (Padrão do Sistema / Integrada)",
        "cam_device_1": "Câmera 1 (Dispositivo USB / Secundário)",
        "cam_device_2": "Câmera 2 (Dispositivo Adicional)",
        "cam_device_3": "Câmera 3 (Dispositivo Adicional)",

        # HUD Blocked
        "hud_blocked": "BLOQUEADO",

        # User Manager & Database
        "user_mgr_title": "Gerenciador de Usuários",
        "user_mgr_subtitle": "Cadastros biométricos, fotos e controle de acesso",
        "user_search_placeholder": "Buscar por nome, documento, telefone, email...",
        "filter_all_roles": "Todas as Funções",
        "filter_all_statuses": "Todos os Status",
        "status_active": "Ativo",
        "status_inactive": "Inativo / Bloqueado",
        "stat_total": "Total",
        "btn_export_users": "Exportar CSV",
        "btn_new_user": "+ Novo Cadastro",
        "col_avatar": "Foto",
        "col_doc": "Documento/Apto",
        "col_contact": "Contato",
        "col_status": "Status",
        "col_actions": "Ações",
        "btn_edit": "Editar",
        "btn_full_register": "Cadastro Completo...",
        "btn_manage_users": "Gerenciar...",
        "menu_users": "Usuários",
        "menu_manage_users": "Gerenciar Banco de Usuários...",
        "menu_new_user": "Novo Cadastro de Pessoa...",
        "menu_export_users": "Exportar Lista de Usuários (CSV)...",

        # User Edit / Create Dialog
        "user_dialog_create_title": "Novo Cadastro de Pessoa",
        "user_dialog_edit_title": "Editar Dados do Usuário",
        "user_avatar_hint": "Foto de perfil (Face para biometria)",
        "user_avatar_saved": "Foto biométrica salva.",
        "btn_upload_photo": "Carregar Foto de Arquivo...",
        "btn_cam_capture": "Capturar da Câmera",
        "select_photo_title": "Selecionar Foto da Pessoa",
        "user_doc_label": "Documento / Matrícula / Apto:",
        "user_doc_placeholder": "ex: Apto 102, CPF, ou Crachá",
        "user_phone_label": "Telefone / WhatsApp:",
        "user_phone_placeholder": "ex: (11) 98765-4321",
        "user_email_label": "E-mail:",
        "user_email_placeholder": "ex: pessoa@exemplo.com",
        "user_status_label": "Status de Acesso:",
        "user_notes_label": "Observações / Notas:",
        "user_notes_placeholder": "Horários permitidos, detalhes, etc.",
        "enroll_status_processing": "Processando imagem...",
        "enroll_status_detecting": "Analisando traços faciais...",
        "enroll_err_file_not_found": "Arquivo não encontrado.",
        "enroll_err_invalid_image": "Formato de imagem inválido ou ilegível.",
        "enroll_err_no_input": "Nenhuma imagem informada.",
        "enroll_err_dlib_unavailable": "Módulo de reconhecimento facial não carregado.",
        "enroll_err_no_face": "Nenhum rosto encontrado na foto. Use uma foto clara de frente.",
        "enroll_err_encoding_failed": "Falha ao gerar biometria facial.",

        # Update Flow v1.0.7
        "update_install_now": "Instalar Atualização",
        "update_ready_title": "Atualização Pronta",
        "update_instruction_msg": "A atualização para a versão {version} foi baixada!\n\nAo clicar em OK, o Sentinel será fechado para instalar a atualização silenciosamente.\n\nPor favor, aguarde alguns segundos após o fechamento e abra o Sentinel novamente pelo atalho na Área de Trabalho ou no Menu Iniciar.",

        # History & Facial Recordings Center v1.0.8
        "btn_full_history": "Histórico Completo...",
        "menu_view_history": "Histórico Completo de Eventos...",
        "history_dialog_title": "Histórico de Registros Faciais",
        "history_dialog_subtitle": "Histórico completo de entradas, saídas e capturas faciais",
        "history_search_placeholder": "Buscar por nome ou emoção...",
        "filter_all_directions": "Todas as Direções",
        "filter_enter": "Entrada",
        "filter_exit": "Saída",
        "filter_limit_100": "Últimos 100",
        "filter_limit_250": "Últimos 250",
        "filter_limit_500": "Últimos 500",
        "filter_limit_all": "Todos os Registros",
        "stat_total_events": "Total de Registros",
        "stat_enters": "Entradas",
        "stat_exits": "Saídas",
        "stat_unique_persons": "Pessoas Únicas",
        "col_log_thumb": "Foto",
        "col_log_time": "Data / Hora",
        "col_log_name": "Nome",
        "col_log_direction": "Direção",
        "col_log_emotion": "Emoção",
        "col_log_actions": "Ações",
        "btn_delete_record": "Excluir",
        "confirm_delete_record_title": "Excluir Registro",
        "confirm_delete_record_msg": "Deseja excluir permanentemente este registro facial de {name} ({time})?",
        "lateral_cleared_status": "Aba lateral limpa para a sessão atual. Os registros continuam salvos no Histórico Completo.",
        "image_preview_title": "Visualização do Registro Facial - {name}",
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

        # Settings Menu & Dialog
        "menu_settings": "Settings",
        "menu_open_settings": "Open Settings...",
        "menu_fps_settings": "Camera Frame Rate (FPS)...",
        "menu_lang_settings": "Interface Language...",
        "settings_dialog_title": "Sentinel Settings",
        "settings_tab_general": "General",
        "settings_tab_camera": "Camera & Performance",
        "settings_lang_label": "Interface Language:",
        "settings_lang_desc": "Change application language on the fly.",
        "settings_fps_label": "Camera Frame Rate (FPS):",
        "settings_fps_desc": "Camera capture FPS limit. 30 FPS is recommended. Lower to 15 or 20 FPS to reduce CPU usage.",
        "settings_version_label": "Installed Version:",
        "settings_version_info": "Sentinel v{version} (Native x64 Build)",
        "settings_engine_info": "Engine: dlib C++ & PySide6 & BLAS Vectorized Search",
        "settings_btn_check_update": "Check for Updates Now",
        "settings_btn_save": "Save and Close",

        # Theme
        "settings_theme_label": "Appearance & Theme:",
        "settings_theme_desc": "Switch between Dark Mode and Light (Day) Mode.",
        "theme_dark": "Dark Mode (Default)",
        "theme_light": "Light Mode (Day)",

        # Camera Input
        "settings_cam_label": "Camera Input Device:",
        "settings_cam_desc": "Select the webcam or video sensor used by Sentinel.",
        "cam_device_0": "Camera 0 (System Default / Integrated)",
        "cam_device_1": "Camera 1 (USB Device / Secondary)",
        "cam_device_2": "Camera 2 (Additional Device)",
        "cam_device_3": "Camera 3 (Additional Device)",

        # HUD Blocked
        "hud_blocked": "BLOCKED",

        # User Manager & Database
        "user_mgr_title": "User Management Database",
        "user_mgr_subtitle": "Biometric profiles, avatars, and access control",
        "user_search_placeholder": "Search by name, document, phone, email...",
        "filter_all_roles": "All Roles",
        "filter_all_statuses": "All Statuses",
        "status_active": "Active",
        "status_inactive": "Inactive / Blocked",
        "stat_total": "Total",
        "btn_export_users": "Export CSV",
        "btn_new_user": "+ New User",
        "col_avatar": "Photo",
        "col_doc": "Document/Unit",
        "col_contact": "Contact",
        "col_status": "Status",
        "col_actions": "Actions",
        "btn_edit": "Edit",
        "btn_full_register": "Full Registration...",
        "btn_manage_users": "Manage...",
        "menu_users": "Users",
        "menu_manage_users": "Manage User Database...",
        "menu_new_user": "New User Registration...",
        "menu_export_users": "Export User List (CSV)...",

        # User Edit / Create Dialog
        "user_dialog_create_title": "New User Registration",
        "user_dialog_edit_title": "Edit User Profile",
        "user_avatar_hint": "Profile avatar (Face for biometrics)",
        "user_avatar_saved": "Biometric avatar saved.",
        "btn_upload_photo": "Upload Photo File...",
        "btn_cam_capture": "Capture from Camera",
        "select_photo_title": "Select Person's Photo",
        "user_doc_label": "Document / ID / Unit:",
        "user_doc_placeholder": "e.g. Unit 102, ID, or Badge",
        "user_phone_label": "Phone / WhatsApp:",
        "user_phone_placeholder": "e.g. +1 555-0199",
        "user_email_label": "Email:",
        "user_email_placeholder": "e.g. person@example.com",
        "user_status_label": "Access Status:",
        "user_notes_label": "Notes / Observations:",
        "user_notes_placeholder": "Authorized hours, security details, etc.",
        "enroll_status_processing": "Processing image...",
        "enroll_status_detecting": "Detecting facial landmarks...",
        "enroll_err_file_not_found": "File not found.",
        "enroll_err_invalid_image": "Invalid or unreadable image file.",
        "enroll_err_no_input": "No input image provided.",
        "enroll_err_dlib_unavailable": "Face recognition engine unavailable.",
        "enroll_err_no_face": "No face found in photo. Please use a clear front-facing portrait.",
        "enroll_err_encoding_failed": "Failed to generate facial biometrics.",

        # Update Flow v1.0.7
        "update_install_now": "Install Update",
        "update_ready_title": "Update Ready",
        "update_instruction_msg": "The update to version {version} is ready!\n\nClicking OK will close Sentinel and install the update silently in the background.\n\nPlease wait a few seconds after Sentinel closes, then reopen Sentinel from your Desktop or Start Menu shortcut.",

        # History & Facial Recordings Center v1.0.8
        "btn_full_history": "Full History...",
        "menu_view_history": "Full Event History...",
        "history_dialog_title": "Facial Recordings History",
        "history_dialog_subtitle": "Complete history of entries, exits, and saved facial captures",
        "history_search_placeholder": "Search by name or emotion...",
        "filter_all_directions": "All Directions",
        "filter_enter": "Entry",
        "filter_exit": "Exit",
        "filter_limit_100": "Last 100",
        "filter_limit_250": "Last 250",
        "filter_limit_500": "Last 500",
        "filter_limit_all": "All Records",
        "stat_total_events": "Total Records",
        "stat_enters": "Entries",
        "stat_exits": "Exits",
        "stat_unique_persons": "Unique Persons",
        "col_log_thumb": "Photo",
        "col_log_time": "Date / Time",
        "col_log_name": "Name",
        "col_log_direction": "Direction",
        "col_log_emotion": "Emotion",
        "col_log_actions": "Actions",
        "btn_delete_record": "Delete",
        "confirm_delete_record_title": "Delete Record",
        "confirm_delete_record_msg": "Permanently delete this facial record for {name} ({time})?",
        "lateral_cleared_status": "Lateral feed cleared for current session. Records remain saved in Full History.",
        "image_preview_title": "Facial Record Preview - {name}",
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

        # Settings Menu & Dialog
        "menu_settings": "Configuración",
        "menu_open_settings": "Abrir Configuración...",
        "menu_fps_settings": "Tasa de Cuadros (FPS)...",
        "menu_lang_settings": "Idioma de la Interfaz...",
        "settings_dialog_title": "Configuración de Sentinel",
        "settings_tab_general": "General",
        "settings_tab_camera": "Cámara y Rendimiento",
        "settings_lang_label": "Idioma de la Interfaz:",
        "settings_lang_desc": "Cambie el idioma de la aplicación al instante.",
        "settings_fps_label": "Tasa de Cuadros de la Cámara (FPS):",
        "settings_fps_desc": "Límite de FPS de captura. Se recomienda 30 FPS. Baje a 15 o 20 FPS para reducir el uso de CPU.",
        "settings_version_label": "Versión Instalada:",
        "settings_version_info": "Sentinel v{version} (Compilación Nativa x64)",
        "settings_engine_info": "Motor: dlib C++ & PySide6 & Búsqueda Vectorial BLAS",
        "settings_btn_check_update": "Buscar Actualizaciones Ahora",
        "settings_btn_save": "Guardar y Cerrar",

        # Theme
        "settings_theme_label": "Apariencia y Tema:",
        "settings_theme_desc": "Cambie entre el Modo Oscuro y el Modo Claro (Día).",
        "theme_dark": "Modo Oscuro (Predeterminado)",
        "theme_light": "Modo Claro (Día)",

        # Camera Input
        "settings_cam_label": "Dispositivo de Cámara:",
        "settings_cam_desc": "Seleccione el sensor de video o cámara web a utilizar.",
        "cam_device_0": "Cámara 0 (Predeterminada del Sistema / Integrada)",
        "cam_device_1": "Cámara 1 (Dispositivo USB / Secundario)",
        "cam_device_2": "Cámara 2 (Dispositivo Adicional)",
        "cam_device_3": "Cámara 3 (Dispositivo Adicional)",

        # HUD Blocked
        "hud_blocked": "BLOQUEADO",

        # User Manager & Database
        "user_mgr_title": "Gestor de Usuarios",
        "user_mgr_subtitle": "Perfiles biométricos, fotos y control de acceso",
        "user_search_placeholder": "Buscar por nombre, documento, teléfono, email...",
        "filter_all_roles": "Todos los Roles",
        "filter_all_statuses": "Todos los Estados",
        "status_active": "Activo",
        "status_inactive": "Inactivo / Bloqueado",
        "stat_total": "Total",
        "btn_export_users": "Exportar CSV",
        "btn_new_user": "+ Nuevo Usuario",
        "col_avatar": "Foto",
        "col_doc": "Documento/Apto",
        "col_contact": "Contacto",
        "col_status": "Estado",
        "col_actions": "Acciones",
        "btn_edit": "Editar",
        "btn_full_register": "Registro Completo...",
        "btn_manage_users": "Gestionar...",
        "menu_users": "Usuarios",
        "menu_manage_users": "Gestionar Base de Usuarios...",
        "menu_new_user": "Nuevo Registro de Persona...",
        "menu_export_users": "Exportar Lista de Usuarios (CSV)...",

        # User Edit / Create Dialog
        "user_dialog_create_title": "Nuevo Registro de Persona",
        "user_dialog_edit_title": "Editar Perfil de Usuario",
        "user_avatar_hint": "Foto de perfil (Rostro para biometría)",
        "user_avatar_saved": "Foto biométrica guardada.",
        "btn_upload_photo": "Cargar Foto de Archivo...",
        "btn_cam_capture": "Capturar de Cámara",
        "select_photo_title": "Seleccionar Foto de la Persona",
        "user_doc_label": "Documento / Matrícula / Apto:",
        "user_doc_placeholder": "ej: Apto 102, DNI o Credencial",
        "user_phone_label": "Teléfono / WhatsApp:",
        "user_phone_placeholder": "ej: +34 600 000 000",
        "user_email_label": "Correo electrónico:",
        "user_email_placeholder": "ej: persona@ejemplo.com",
        "user_status_label": "Estado de Acceso:",
        "user_notes_label": "Observaciones / Notas:",
        "user_notes_placeholder": "Horarios autorizados, detalles, etc.",
        "enroll_status_processing": "Procesando imagen...",
        "enroll_status_detecting": "Analizando rasgos faciales...",
        "enroll_err_file_not_found": "Archivo no encontrado.",
        "enroll_err_invalid_image": "Formato de imagen inválido o ilegible.",
        "enroll_err_no_input": "Ninguna imagen proporcionada.",
        "enroll_err_dlib_unavailable": "Motor de reconocimiento facial no disponible.",
        "enroll_err_no_face": "No se encontró ningún rostro en la foto. Use una foto frontal clara.",
        "enroll_err_encoding_failed": "Error al generar biometría facial.",

        # Update Flow v1.0.7
        "update_install_now": "Instalar Actualización",
        "update_ready_title": "Actualización Lista",
        "update_instruction_msg": "¡La atualização a la versión {version} ha sido descargada!\n\nAl hacer clic en OK, Sentinel se cerrará para instalar la actualización silenciosamente en segundo plano.\n\nPor favor, espere unos segundos tras el cierre y abra Sentinel nuevamente desde el acceso directo del Escritorio o Menú Inicio.",

        # History & Facial Recordings Center v1.0.8
        "btn_full_history": "Historial Completo...",
        "menu_view_history": "Historial Completo de Eventos...",
        "history_dialog_title": "Historial de Grabaciones Faciales",
        "history_dialog_subtitle": "Historial completo de entradas, salidas y capturas faciales",
        "history_search_placeholder": "Buscar por nombre o emoción...",
        "filter_all_directions": "Todas las Direcciones",
        "filter_enter": "Entrada",
        "filter_exit": "Salida",
        "filter_limit_100": "Últimos 100",
        "filter_limit_250": "Últimos 250",
        "filter_limit_500": "Últimos 500",
        "filter_limit_all": "Todos los Registros",
        "stat_total_events": "Total de Registros",
        "stat_enters": "Entradas",
        "stat_exits": "Salidas",
        "stat_unique_persons": "Personas Únicas",
        "col_log_thumb": "Foto",
        "col_log_time": "Fecha / Hora",
        "col_log_name": "Nombre",
        "col_log_direction": "Dirección",
        "col_log_emotion": "Emoción",
        "col_log_actions": "Acciones",
        "btn_delete_record": "Eliminar",
        "confirm_delete_record_title": "Eliminar Registro",
        "confirm_delete_record_msg": "¿Desea eliminar permanentemente este registro facial de {name} ({time})?",
        "lateral_cleared_status": "Pestaña lateral limpiada para la sesión actual. Los registros siguen guardados en el Historial Completo.",
        "image_preview_title": "Vista Previa de Grabación Facial - {name}",
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
