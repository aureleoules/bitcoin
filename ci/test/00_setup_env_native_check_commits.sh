#!/usr/bin/env bash
#
# Copyright (c) 2019-2021 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

export LC_ALL=C.UTF-8

export DOCKER_NAME_TAG="ubuntu:22.04"
export CONTAINER_NAME=ci_check_commits
export PACKAGES="clang llvm python3-zmq libevent-dev bsdmainutils libboost-dev libdb5.3++-dev libminiupnpc-dev libnatpmp-dev libzmq3-dev libsqlite3-dev"
export USE_VALGRIND=0
export NO_DEPENDS=1
export CHECK_ALL_COMMITS_COMPILE=true
export RUN_FUNCTIONAL_TESTS=false
export RUN_UNIT_TESTS=false
export GOAL="install"
# Temporarily pin dwarf 4, until valgrind can understand clang's dwarf 5
export BITCOIN_CONFIG="--enable-zmq --with-incompatible-bdb --with-gui=no CC=clang CXX=clang++"
