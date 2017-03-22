from icapservice.content import decoders
import os
test_dir = os.path.dirname(os.path.realpath(__file__))

def test_brotli():    
    with open(test_dir + '/compressed_files/alice.txt.br', 'rb') as f:
        alice = f.read()
    decode_brotli = decoders['br']
    alice_in_wonderland = ''
    for chunk in decode_brotli(alice):
        alice_in_wonderland += chunk
    assert 'Mock Turtle' in alice_in_wonderland
