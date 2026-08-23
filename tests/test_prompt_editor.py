from lwa_mcp.prompt_editor import PromptEditor


def test_prompt_editor_supports_multiline_insert_delete_and_navigation():
    editor = PromptEditor()
    editor.insert("ab")
    editor.left()
    editor.insert("X")
    editor.newline()
    editor.insert("cd")
    assert editor.text == "aX\ncdb"

    editor.home()
    editor.delete()
    assert editor.text == "aX\ndb"
    editor.backspace()
    assert editor.text == "aXdb"

    editor.end()
    assert editor.cursor == 4


def test_prompt_editor_vertical_navigation_preserves_column():
    editor = PromptEditor()
    editor.insert("one\ntwo\nthree")
    editor.home()
    editor.up()
    editor.right()
    assert editor.text[editor.cursor] == "w"
    editor.down()
    assert editor.cursor == 9


def test_prompt_editor_shift_arrows_select_and_replace_text():
    editor = PromptEditor()
    editor.insert("hello")
    editor.move_left(select=True)
    editor.move_left(select=True)
    assert editor.selected_text() == "lo"
    editor.insert("y")
    assert editor.text == "hely"
