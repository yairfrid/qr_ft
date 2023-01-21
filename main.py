import click
import cv2

import qr_client
import qr_server
from utils import FIRST_CAMERA


@click.group()
def cli():
    pass

@click.command()
@click.argument('path')
def client(path: str):
    """Run the client to read a file from qr to a path"""
    cap = cv2.VideoCapture(FIRST_CAMERA)
    qr_client.read_file_to_path(cap, path)

@click.command()
@click.argument('path')
def server(path: str):
    """Run the server to write a file to qr to a path"""
    cap = cv2.VideoCapture(FIRST_CAMERA)
    qr_server.send_file_from_path(cap, path)


if __name__ == '__main__':
    # Add commands to click cli https://click.palletsprojects.com/en/8.1.x/
    cli.add_command(client)
    cli.add_command(server)
    cli()
