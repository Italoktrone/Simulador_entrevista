extends RefCounted
## Tema nativo: no necesita imágenes ni recursos externos.

const INK = Color("e9f1f7")
const MUTED = Color("9aafc3")
const ACCENT = Color("63deca")
const SURFACE = Color("142132")


static func box(color: Color, border: Color = Color("293c50"), padding: int = 16) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = color
	style.border_color = border
	style.set_border_width_all(1)
	style.set_corner_radius_all(10)
	style.content_margin_left = padding
	style.content_margin_right = padding
	style.content_margin_top = padding
	style.content_margin_bottom = padding
	return style


static func build() -> Theme:
	var theme := Theme.new()
	theme.default_font_size = 15
	for kind in ["Label", "RichTextLabel", "CheckButton", "Button", "LineEdit"]:
		theme.set_color("font_color", kind, INK)
	theme.set_color("default_color", "RichTextLabel", INK)
	theme.set_stylebox("panel", "PanelContainer", box(SURFACE))
	for state in ["normal", "hover", "pressed", "disabled"]:
		var color := Color("1b2e43") if state != "hover" else Color("294258")
		if state == "disabled":
			color = Color("111c2a")
		theme.set_stylebox(state, "Button", box(color, Color("314a60"), 12))
	theme.set_color("font_disabled_color", "Button", Color("657b8e"))
	theme.set_stylebox("focus", "Button", box(Color(0, 0, 0, 0), ACCENT, 0))
	theme.set_stylebox("normal", "LineEdit", box(Color("0d1826"), Color("314a60"), 12))
	theme.set_stylebox("read_only", "LineEdit", box(Color("0d1826"), Color("233446"), 12))
	theme.set_stylebox("focus", "LineEdit", box(Color(0, 0, 0, 0), ACCENT, 0))
	theme.set_color("font_placeholder_color", "LineEdit", MUTED)
	theme.set_color("font_uneditable_color", "LineEdit", MUTED)
	theme.set_color("font_color", "CheckButton", MUTED)
	theme.set_stylebox("background", "ProgressBar", box(Color("142132"), Color("142132"), 0))
	theme.set_stylebox("fill", "ProgressBar", box(ACCENT, ACCENT, 0))
	return theme


static func primary(button: Button) -> void:
	for state in ["normal", "hover", "pressed"]:
		button.add_theme_stylebox_override(state, box(ACCENT.lightened(0.08) if state == "hover" else ACCENT, ACCENT, 12))
	button.add_theme_color_override("font_color", Color("10222c"))
	button.add_theme_color_override("font_hover_color", Color("10222c"))
	button.add_theme_color_override("font_pressed_color", Color("10222c"))
