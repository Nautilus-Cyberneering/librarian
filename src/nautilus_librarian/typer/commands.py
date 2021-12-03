import typer

app = typer.Typer()


@app.command()
def test(echo_string: str):
    """
    It's only used for testing purposes
    """    
    typer.echo(f"Testing main module: {echo_string}")