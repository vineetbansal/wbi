from wbi.commands.hello import main


def test_default_greeting():
    greeting = main(["--greeting", "Howdy", "--num", "2"])
    assert greeting == "Howdy Howdy"
