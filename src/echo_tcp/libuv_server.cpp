#include <uv.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static const char RESP[] =
  "HTTP/1.1 200 OK\r\n"
  "Content-Type: application/json\r\n"
  "Content-Length: 20\r\n"
  "Connection: keep-alive\r\n"
  "\r\n"
  "{\"status\":\"success\"}";

typedef struct client_s {
    uv_tcp_t handle;
    uv_write_t write_req;
} client_t;

static void alloc_cb(uv_handle_t* h, size_t suggested, uv_buf_t* buf){
    static char sbuf[65536];
    (void)h; (void)suggested;
    *buf = uv_buf_init(sbuf, sizeof(sbuf));
}

static void on_write(uv_write_t* req, int status){
    (void)status;
    // keep-alive: ничего не делаем, ждём следующий read
}

static void on_read(uv_stream_t* s, ssize_t nread, const uv_buf_t* buf){
    (void)buf;
    if (nread <= 0) { uv_close((uv_handle_t*)s, NULL); return; }
    client_t* c = (client_t*)s;
    uv_buf_t out = uv_buf_init((char*)RESP, (unsigned int)(sizeof(RESP)-1));
    uv_write(&c->write_req, s, &out, 1, on_write);
}

static void on_conn(uv_stream_t* server, int status){
    if (status < 0) return;
    uv_loop_t* loop = server->loop;
    client_t* c = (client_t*)malloc(sizeof(client_t));
    if (!c) return;
    uv_tcp_init(loop, &c->handle);
    if (uv_accept(server, (uv_stream_t*)&c->handle)==0){
        uv_read_start((uv_stream_t*)&c->handle, alloc_cb, on_read);
    } else {
        uv_close((uv_handle_t*)&c->handle, NULL);
        free(c);
    }
}

int main(int argc, char** argv){
    const char* host="0.0.0.0";
    int port=45900;
    for (int i=1;i<argc;i++){
        if(!strcmp(argv[i],"--port") && i+1<argc) port=atoi(argv[++i]);
    }

    uv_loop_t* loop = uv_default_loop();
    uv_tcp_t srv; uv_tcp_init(loop, &srv);

    struct sockaddr_in addr; uv_ip4_addr(host, port, &addr);
    uv_tcp_bind(&srv, (const struct sockaddr*)&addr, 0);

    int r = uv_listen((uv_stream_t*)&srv, 65535, on_conn);
    if (r) { fprintf(stderr, "listen error: %s\n", uv_strerror(r)); return 1; }

    return uv_run(loop, UV_RUN_DEFAULT);
}
