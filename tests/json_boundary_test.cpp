#include "../native/json_boundary.h"
#include <cassert>
int main(){
  JsonBoundary a;a.append(" {\"message\":\"a } bracket\",\"nested\":[{\"x\":1}]} trailing");
  assert(a.done&&a.text==" {\"message\":\"a } bracket\",\"nested\":[{\"x\":1}]}");
  JsonBoundary b;b.append("{\"a\":\"escaped \\");b.append("\" still string\"}");assert(b.done);
  JsonBoundary c;c.append("This is prose {not JSON}");assert(!c.done&&c.text=="This is prose {not JSON}");
  JsonBoundary d;d.append("{\"a\":{");assert(!d.done);d.append("}}{\"second\":true}");assert(d.done&&d.text=="{\"a\":{}}");
  JsonBoundary e;e.append("{}");e.append("ignored");assert(e.done&&e.text=="{}");
}
