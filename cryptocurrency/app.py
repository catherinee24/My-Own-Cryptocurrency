# Importación de las librerías
import datetime
import hashlib
import json
import requests
from uuid         import uuid4
from flask        import Flask, jsonify, request
from urllib.parse import urlparse
from flask_ngrok  import run_with_ngrok

class Blockchain:
    
  def __init__(self):
    """ Constructor de la clase. """

    self.chain = []
    self.transactions = []
    self.create_block(proof = 1, previous_hash = '0')
    self.nodes = set()
      
  def create_block(self, proof, previous_hash):
    """ Creación de un nuevo bloque. 

      Arguments:
        - proof: Nounce del bloque actual.
        - previous_hash: Hash del bloque previo.

      Returns: 
        - block: Nuevo bloque creado. 
      """

    block = { 'index'         : len(self.chain)+1,
              'timestamp'     : str(datetime.datetime.now()),
              'proof'         : proof,
              'previous_hash' : previous_hash,
              'transactions'  : self.transactions}
    self.transactions = []
    self.chain.append(block)
    return block

  def get_previous_block(self):
    """ Obtención del bloque previo de la Blockchain.
    
      Returns:
        - Obtención del último bloque de la Blockchain. """

    return self.chain[-1]
  
  def proof_of_work(self, previous_proof):     
    """ Protocolo de concenso Proof of Work (PoW).
    
      Arguments:
        - previous_proof: Nounce del bloque previo.

      Returns:
        - new_proof: Devolución del nuevo nounce obtenido con PoW. """

    new_proof = 1
    check_proof = False
    while check_proof is False:
        hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
        if hash_operation[:4] == '0000':
            check_proof = True
        else: 
            new_proof += 1
    return new_proof
  
  def hash(self, block):
    """ Cálculo del hash de un bloque.
    
    Arguments:
        - block: Identifica a un bloque de la Blockchain.
    
    Returns:
        - hash_block: Devuelve el hash del bloque """

    encoded_block = json.dumps(block, sort_keys = True).encode()
    hash_block = hashlib.sha256(encoded_block).hexdigest()
    return hash_block
  
  def is_chain_valid(self, chain):
    """ Determina si la Blockchain es válida. 
    
    Arguments:
        - chain: Cadena de bloques que contiene toda la 
                  información de las transacciones.
    
    Returns:
        - True/False: Devuelve un booleano en función de la validez de la 
                      Blockchain. (True = Válida, False = Inválida) """
                      
    previous_block = chain[0]
    block_index = 1
    while block_index < len(chain):
        block = chain[block_index]
        if block['previous_hash'] != self.hash(previous_block):
            return False
        previous_proof = previous_block['proof']
        proof = block['proof']
        hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
        if hash_operation[:4] != '0000':
            return False
        previous_block = block
        block_index += 1
    return True
  
  def add_transaction(self, sender, receiver, amount):
    """ Realización de una transacción.
    
    Arguments:
        - sender: Persona que hace la transacción
        - receiver: Persona que recibe la transacción
        - amount: Cantidad de criptomonedas enviadas

    Returns: 
        - Devolución del índice superior al último bloque
    """

    self.transactions.append({'sender'  : sender,
                              'receiver': receiver, 
                              'amount'  : amount})
    previous_block = self.get_previous_block()
    return previous_block['index'] + 1

  def add_node(self, address):
    """ Nuevo nodo en la Blockchain.
    
      Arguments:
        - address: Dirección del nuevo nodo
    """

    parsed_url = urlparse(address)
    self.nodes.add(parsed_url.netloc)
  
  def replace_chain(self):
    """ Remplazo de la cadena por la cadena más larga, 
    siempre y cuando sea válida. """
    
    network = self.nodes
    longest_chain = None
    max_length = len(self.chain)
    for node in network:
        response = requests.get(f'http://{node}/get_chain')
        if response.status_code == 200:
            length = response.json()['length']
            chain = response.json()['chain']
            if length > max_length and self.is_chain_valid(chain):
                max_length = length
                longest_chain = chain
    if longest_chain: 
        self.chain = longest_chain
        return True
    return False

#######################################################################################################

# Minado de un Bloque de la Cadena

# Crear una aplicación web
app = Flask(__name__)
run_with_ngrok(app)  

# Si se obtiene un error 500, actualizar flask, reiniciar spyder y ejecutar la siguiente línea
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Crear la dirección del nodo en el puerto 5000
node_address = str(uuid4()).replace('-', '')

# Crear una Blockchain
blockchain = Blockchain()


@app.route('/mine_block', methods=['GET'])
def mine_block():
  """ Minado de un nuevo bloque """ 

  previous_block = blockchain.get_previous_block()
  previous_proof = previous_block['proof']
  proof = blockchain.proof_of_work(previous_proof)
  previous_hash = blockchain.hash(previous_block)
  blockchain.add_transaction(sender = node_address, receiver = "catellaTech", amount = 10)
  block = blockchain.create_block(proof, previous_hash)
  response = {'message'       : '¡Felicidades crack, nuevo bloque minado!', 
              'index'         : block['index'],
              'timestamp'     : block['timestamp'],
              'proof'         : block['proof'],
              'previous_hash' : block['previous_hash'],
              'transactions'  : block['transactions']}
  return jsonify(response), 200

@app.route('/get_chain', methods=['GET'])
def get_chain():
  """ Obtención de la cadena de bloques al completo """

  response = {'chain'   : blockchain.chain, 
              'length'  : len(blockchain.chain)}
  return jsonify(response), 200

@app.route('/is_valid', methods = ['GET'])
def is_valid():
  """ Comprobación de si la cadena de bloques es válida """

  is_valid = blockchain.is_chain_valid(blockchain.chain)
  if is_valid:
      response = {'message' : 'Todo correcto. La cadena de bloques es válida.'}
  else:
      response = {'message' : 'UPS. La cadena de bloques NO es válida.'}
  return jsonify(response), 200  

@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
  """ Añadir una nueva transacción a la cadena de bloques """

  json = request.get_json()
  transaction_keys = ['sender', 'receiver', 'amount']
  if not all(key in json for key in transaction_keys):
      return 'Faltan algunos elementos de la transacción', 400
  index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
  response = {'message': f'La transacción será añadida al bloque {index}'}
  return jsonify(response), 201
    
# Descentralización de la Cadena de Bloques

# Conectar nuevos nodos
@app.route('/connect_node', methods = ['POST'])
def connect_node():
  json = request.get_json()
  nodes = json.get('nodes')
  if nodes is None: 
      return 'No hay nodos para añadir', 400
  for node in nodes:
      blockchain.add_node(node)
  response = {'message'     : 'Todos los nodos han sido conectados. La Blockchain de CatellaCoin contiene ahora los nodos siguientes: ',
              'total_nodes' : list(blockchain.nodes)}
  return jsonify(response), 201

@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
  """ Reemplazar la cadena por la más larga (si es necesario) """

  is_chain_replaced = blockchain.replace_chain()
  if is_chain_replaced:
      response = {'message' : 'Los nodos tenían diferentes cadenas, se ha remplazado por la Blockchain más larga.',
                  'new_chain': blockchain.chain}
  else:
      response = {'message'       : 'Todo correcto. La Blockchain en todos los nodos ya es la más larga.',
                  'actual_chain'  : blockchain.chain}
  return jsonify(response), 200