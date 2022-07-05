#!/usr/bin/env python3
# Copyright (c) 2022 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

"""Test wallet import on pruned node."""
import os

from test_framework.util import assert_raises_rpc_error
from test_framework.blocktools import create_block
from test_framework.blocktools import create_coinbase
from test_framework.test_framework import BitcoinTestFramework

from test_framework.script import (
    CScript,
    OP_RETURN,
    OP_TRUE,
)

class WalletPruningTest(BitcoinTestFramework):
    nTime = 0
    def mine_large_blocks(self, node, n):
        # Get the block parameters for the first block
        best_block = node.getblock(node.getbestblockhash())
        height = int(best_block["height"]) + 1
        self.nTime = max(self.nTime, int(best_block["time"])) + 1
        previousblockhash = int(best_block["hash"], 16)
        big_script = CScript([OP_RETURN] + [OP_TRUE] * 950000)
        for _ in range(n):
            block = create_block(hashprev=previousblockhash, ntime=self.nTime, coinbase=create_coinbase(height, script_pubkey=big_script))
            block.solve()

            # Submit to the node
            node.submitblock(block.serialize().hex())

            previousblockhash = block.sha256
            height += 1

            # Simulate 10 minutes of work time per block
            # Important for matching a timestamp with a block +- some window
            self.nTime += 600
            for n in self.nodes:
                if n.running:
                    n.setmocktime(self.nTime) # Update node's time to accept future blocks

    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 2
        self.extra_args = [
            [], # node dedicated to mining
            ['-prune=550'], # node dedicated to testing pruning
        ]

    def setup_nodes(self):
        self.add_nodes(self.num_nodes, extra_args=self.extra_args)
        self.start_node(0)

    def setup_network(self):
        self.setup_nodes()

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def create_big_chain(self):
        self.log.info("Generating a long chain of blocks...")
        # Generate 288 light blocks, the minimum required to stay on disk with prune enabled
        # do not sync
        self.generate(self.nodes[0], 288, sync_fun=lambda: None)

        # Generate large blocks to make sure we have enough to test chain pruning
        self.mine_large_blocks(self.nodes[0], 600)

    def test_wallet_import_pruned_test(self):
        self.log.info("Make sure we can import wallet when pruned and required blocks are still available")

        wname = "wallet_pruned.dat"

        # export wallet
        self.nodes[0].dumpwallet(os.path.join(self.nodes[0].datadir, wname))
        # import wallet
        self.nodes[1].importwallet(os.path.join(self.nodes[0].datadir, wname))

        # mine some blocks, pruning should not have removed the block
        self.mine_large_blocks(self.nodes[0], 5)
        self.sync_all()

        # import wallet, should still work
        self.nodes[1].importwallet(os.path.join(self.nodes[0].datadir, wname))
        self.log.info("Wallet successfully imported on pruned node")

    def test_wallet_import_pruned_with_missing_blocks(self):
        self.log.info("Make sure we cannot import wallet when pruned and required blocks are not available")

        wname = "wallet_init.dat"

        # get birthheight of wallet
        with open(os.path.join(self.nodes[1].datadir, wname), 'r', encoding="utf8") as f:
            for line in f:
                if line.startswith('# * Best block at time of backup'):
                    wallet_birthheight = int(line.split(' ')[9])
                    break

        assert_raises_rpc_error(-1, "Block not available (pruned data)", self.nodes[1].getblock, self.nodes[1].getblockhash(wallet_birthheight))

        # make sure wallet cannot be imported because of missing blocks
        assert_raises_rpc_error(-4, "Pruned blocks from height 876 required to import keys. Use RPC call getblockchaininfo to determine your pruned height.", self.nodes[1].importwallet, os.path.join(self.nodes[1].datadir, wname))

    def run_test(self):
        self.log.info("Warning! This test requires ~1.5GB of disk space")

        self.nodes[0].createwallet(wallet_name="wallet_init", descriptors=self.options.descriptors, load_on_startup=True)
        self.nodes[0].dumpwallet(os.path.join(self.nodes[0].datadir, "wallet_init.dat"))
        self.create_big_chain()

        # connect mid-test node1
        self.start_node(1)
        self.nodes[1].setmocktime(self.nodes[0].getblock(self.nodes[0].getbestblockhash())['time'])
        self.connect_nodes(1, 0)
        self.sync_blocks(timeout=120)
        self.nodes[0].createwallet(wallet_name="wallet", descriptors=self.options.descriptors, load_on_startup=True)

        self.test_wallet_import_pruned_test()
        self.test_wallet_import_pruned_with_missing_blocks()

        self.log.info("Done")

if __name__ == '__main__':
    WalletPruningTest().main()
