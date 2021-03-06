from typing import List

from AccountModel import AccountModel
from Block import Block
from Transaction import Transaction
from Utils import Utils
from ProofOfStake import ProofOfStake
from Wallet import Wallet


class Blockchain:
    def __init__(self):
        # add genesis block
        self.blocks = [Block.genesis()]
        self.accountModel = AccountModel()
        self.pos = ProofOfStake()

    # add a block to blockchain
    def addBlock(self, block: Block):
        self.executeTransactions(block.transactions)
        self.blocks.append(block)

    def toJson(self):
        data = {}
        jsonBlocks = []
        for block in self.blocks:
            jsonBlocks.append(block.toJson())
        data["blocks"] = jsonBlocks
        return data

    # validate if blockCount matches with the number of added blocks in blockchain
    def blockCountValid(self, block):
        return self.blocks[-1].blockCount == block.blockCount - 1

    # validate if the prev hash is the last block's hash in blockchain
    def lastBlockHashValid(self, block):
        lastBlockHash = Utils.hash(self.blocks[-1].payload()).hexdigest()
        return block.lastHash == lastBlockHash

    # get transactions can be spent
    def getCoveredTransactions(self, transactions):
        coveredTransactions = []
        for transaction in transactions:
            if self.transactionCovered(transaction):
                coveredTransactions.append(transaction)
            else:
                print("Transaction is not covered by sender")
        return coveredTransactions

    # validate if tx can be spent
    def transactionCovered(self, transaction):
        # exchange tx should be always valid
        if transaction.type == "EXCHANGE":
            return True
        senderBalance = self.accountModel.getBalance(transaction.senderPubKey)
        return senderBalance >= transaction.amount

    # execute all transactions of a block
    def executeTransactions(self, transactions):
        for tx in transactions:
            self.executeTransaction(tx)

    # execute one transaction
    def executeTransaction(self, transaction: Transaction):
        sender = transaction.senderPubKey
        receiver = transaction.receiverPubKey
        amount = transaction.amount
        if transaction.type == 'STAKE':
            if sender == receiver:
                self.pos.update(sender, amount)
                self.accountModel.updateBalance(sender, -amount)
        else:
            self.accountModel.updateBalance(sender, -amount)
            self.accountModel.updateBalance(receiver, amount)

    # find the next forger
    def findNextForger(self):
        lastBlockHash = Utils.hash(self.blocks[-1].payload()).hexdigest()
        nextForger = self.pos.getForger(lastBlockHash)
        return nextForger 

    # create a block and add to blockchain
    def createBlock(self, pooledTransactions, forgerWallet: Wallet):
        coveredTransactions = self.getCoveredTransactions(pooledTransactions)
        self.executeTransactions(coveredTransactions)
        newBlock = forgerWallet.createBlock(coveredTransactions, Utils.hash(self.blocks[-1].payload()).hexdigest(), len(self.blocks))
        self.blocks.append(newBlock)
        return newBlock

    # check if tx already exists in blockchain
    def transactionExists(self, transaction):
        for block in self.blocks:
            for tx in block.transactions:
                if transaction.equals(tx):
                    return True
        return False

    # check if the supposed forger of the block is valid
    def forgerValid(self, block: Block):
        forgerPubKey = self.pos.getForger(block.lastHash)
        proposedBlockForger = block.forger
        return forgerPubKey == proposedBlockForger

    # check if to-be-added transactions are valid
    def transactionsValid(self, proposingTransactions):
        coveredTransactions = self.getCoveredTransactions(proposingTransactions)
        return len(proposingTransactions) == len(coveredTransactions)