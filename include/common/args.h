//
// Created by Kirill Zhukov on 9/14/25.
//

#ifndef ARGS_H
#define ARGS_H

#include <string>
#include <cstdint>

struct BenchArgs {
    std::string host = "0.0.0.0";
    uint16_t port = 45900;
    int threads = 4;
    bool reuse_port = false;
};

inline BenchArgs parse_args(int argc, char** argv) {
    BenchArgs a;
    for (int i=1;i<argc;i++){
        std::string s(argv[i]);
        auto next=[&](std::string& dst){ if(i+1<argc) dst=argv[++i]; };
        if (s=="--host") next(a.host);
        else if (s=="--port"){ std::string v; next(v); a.port=uint16_t(std::stoi(v)); }
        else if (s=="--threads"){ std::string v; next(v); a.threads=std::stoi(v); }
        else if (s=="--reuseport") a.reuse_port = true;
    }
    return a;
}

#endif //ARGS_H
