from wbi.commands.goodbye import main


def test_default_greeting():
    greeting = main([])
    assert greeting == "Goodbye Goodbye Goodbye"
