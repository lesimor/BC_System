import hashlib
import json
from time import time
from urllib.parse import urlparse
import requests
from uuid import uuid4


class BlockChain(object):

    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        self.new_block(previous_hash=1, proof=100)  # genesis block

    @property
    def last_block(self):
        return self.chain[-1]

    def new_block(self, proof, previous_hash=None):

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        self.current_transactions = []
        self.chain.append(block)

        return block

    def new_transaction(self, sender, recipient, amount):

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index'] + 1

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            print("Last block: {}".format(last_block))
            print("block: {}".format(block))
            print("="*20)

            # Hash 체크
            if block['previous_hash'] != self.hash(last_block):
                return False

            # POW 검증
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        neighbors = self.nodes
        new_chain = None

        # 길이 더 긴 체인만 볼 것.
        max_length = len(self.chain)

        for node in neighbors:
            print('get_response')
            response = requests.get('http://{}/chain'.format(node))
            print('response return')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # 체인의 길이가 더 길지 그리고 chain이 유효한지 검사
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False

    def proof_of_work(self, last_proof):

        proof = 0

        while self.valid_proof(last_proof, proof) is False:
            print("last proof: {}".format(last_proof))
            print("try proof: {}".format(proof))
            proof += 1

        return proof

    @staticmethod
    def hash(block):

        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def valid_proof(last_proof, proof):

        guess = '{}{}'.format(last_proof, proof).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash[:4] == "0000"
