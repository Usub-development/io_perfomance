#include "common/args.h"
#include <boost/asio.hpp>
#include <thread>
#include <vector>
#include <functional>
#include <cstring>

using boost::asio::ip::tcp;

static const char RESP[] =
  "HTTP/1.1 200 OK\r\n"
  "Content-Type: application/json\r\n"
  "Content-Length: 20\r\n"
  "Connection: keep-alive\r\n"
  "\r\n"
  "{\"status\":\"success\"}";

struct Session : std::enable_shared_from_this<Session> {
  tcp::socket sock;
  std::array<char, 64*1024> buf{};
  explicit Session(tcp::socket s): sock(std::move(s)) {}
  void start(){ do_read(); }
  void do_read(){
    auto self = shared_from_this();
    sock.async_read_some(boost::asio::buffer(buf),
      [this,self](const boost::system::error_code& ec, std::size_t n){
        if (ec || n==0) return;
        do_write(0, sizeof(RESP)-1);
      });
  }
  void do_write(std::size_t off, std::size_t len){
    auto self = shared_from_this();
    boost::asio::async_write(sock, boost::asio::buffer(RESP+off, len),
      [this,self,off,len](const boost::system::error_code& ec, std::size_t n){
        if (ec) return;
        if (n < len) return do_write(off+n, len-n);
        do_read();
      });
  }
};

int main(int argc, char** argv){
  auto a = parse_args(argc, argv);
  boost::asio::io_context ioc(std::max(1,a.threads));

  tcp::endpoint ep(boost::asio::ip::make_address(a.host), a.port);
  tcp::acceptor acc(ioc);
  acc.open(ep.protocol());
  acc.set_option(tcp::acceptor::reuse_address(true));
#ifdef SO_REUSEPORT
  if (a.reuse_port) {
    int one=1; ::setsockopt(acc.native_handle(), SOL_SOCKET, SO_REUSEPORT, &one, sizeof(one));
  }
#endif
  acc.bind(ep);
  acc.listen(65535);

  std::function<void()> do_accept;
  do_accept = [&]{
    acc.async_accept([&](const boost::system::error_code& ec, tcp::socket s){
      if (!ec) std::make_shared<Session>(std::move(s))->start();
      do_accept();
    });
  };
  do_accept();

  std::vector<std::thread> th;
  for(int i=0;i<a.threads-1;i++) th.emplace_back([&]{ ioc.run(); });
  ioc.run();
  for(auto& t: th) t.join();
  return 0;
}
