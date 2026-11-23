#pragma once
#include <cctype>
#include <string>
// Generation boundary only. This is not a JSON/schema/semantic validator.
// A response starting with prose is retained and rejected by Python validation.
struct JsonBoundary {
  std::string text;
  bool started=false,possible=true,quoted=false,escaped=false,done=false;
  int depth=0;
  void append(const std::string& piece) {
    for(char c:piece){
      if(done)break;
      text.push_back(c);
      if(!possible)continue;
      if(!started){
        if(std::isspace(static_cast<unsigned char>(c)))continue;
        if(c!='{'){possible=false;continue;}
        started=true;depth=1;continue;
      }
      if(quoted){
        if(escaped)escaped=false;
        else if(c=='\\')escaped=true;
        else if(c=='"')quoted=false;
        continue;
      }
      if(c=='"')quoted=true;
      else if(c=='{')++depth;
      else if(c=='}'&&--depth==0)done=true;
    }
  }
};
