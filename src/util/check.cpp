// Copyright (c) 2022 The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#if defined(HAVE_CONFIG_H)
#include <config/bitcoin-config.h>
#endif

#include <tinyformat.h>
#include <util/check.h>

#include <cstdio>
#include <cstdlib>
#include <string>
#include <string_view>


NonFatalCheckError::NonFatalCheckError(std::string_view msg, std::string_view file, int line, std::string_view func)
    : std::runtime_error{
          strprintf("Internal bug detected: \"%s\"\n%s:%d (%s)\nPlease report this issue here: %s\n", msg, file, line, func, PACKAGE_BUGREPORT)}
{
}

void assertion_fail(const char* file, int line, const char* func, const char* assertion)
{
    auto str = strprintf("%s:%s %s: Assertion `%s' failed.\n", file, line, func, assertion);
    fwrite(str.data(), 1, str.size(), stderr);
    std::abort();
}
