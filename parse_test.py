import argparse

#parser = argparse.ArgumentParser()
#parser.add_argument('--foo', help='foo help')
#args = parser.parse_args()

parser = argparse.ArgumentParser(description = 'verifies prefix-lists for 3rd parties')
parser.add_argument('--verbose', action='store_true',
                   help='provide additional output for verification')
parser.add_argument('--username', help='username for SSH connections')
parser.add_argument('--password', help='password for SSH username')
args = parser.parse_args()
