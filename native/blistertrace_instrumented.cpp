// Backward-compatible BT1 framing; BT1 STATS precedes each completed response.
// Pinned ExecuTorch v1.0.0. No model/graph changes. Independent request KV reset.
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
#include "json_boundary.h"
#include <executorch/examples/models/llama/runner/runner.h>
#include <executorch/extension/llm/runner/stats.h>
#if defined(ET_USE_THREADPOOL)
#include <executorch/extension/threadpool/threadpool.h>
#endif
using Clock=std::chrono::steady_clock;
double elapsed(Clock::time_point start) {return std::chrono::duration<double,std::milli>(Clock::now()-start).count();}
int main(int argc,char** argv) {
  if(argc!=4)return 2;
  int threads=std::atoi(argv[3]);if(threads<1||threads>4)return 2;
#if defined(ET_USE_THREADPOOL)
  executorch::extension::threadpool::get_threadpool()->_unsafe_reset_threadpool(threads);
#endif
  auto at=Clock::now();
  auto runner=example::create_llama_runner(argv[1],argv[2],std::vector<std::string>{});
  if(!runner||runner->load()!=executorch::runtime::Error::Ok)return 3;
  double load_ms=elapsed(at);
  std::cout<<"BT1 READY 0\n"<<std::flush;
  std::string magic;size_t size;int max_new;
  while(std::cin>>magic>>size>>max_new){
    if(magic!="BT1"||!size||size>32768||max_new<1||max_new>256||std::cin.get()!='\n')return 4;
    std::string prompt(size,'\0');if(!std::cin.read(prompt.data(),size))return 4;
    runner->reset();std::string generated,stats="{}";double callback_first=-1;JsonBoundary boundary;
    executorch::extension::llm::GenerationConfig cfg;
    cfg.echo=false;cfg.max_new_tokens=max_new;cfg.seq_len=2048;cfg.temperature=0;
    at=Clock::now();
    auto error=runner->generate(prompt,cfg,[&](const std::string& token){
      if(callback_first<0)callback_first=elapsed(at);
      boundary.append(token);generated=boundary.text;
      if(boundary.done||generated.size()>8192)runner->stop();
    },[&](const executorch::extension::llm::Stats& s){
      stats=executorch::extension::llm::stats_to_json_string(s);
      stats.pop_back();stats+=",\"tokenization_ms\":"+std::to_string(s.token_encode_end_ms-s.inference_start_ms)+
        ",\"prefill_ms\":"+std::to_string(s.prompt_eval_end_ms-s.model_execution_start_ms)+"}";
    });
    stats.pop_back();stats+=",\"worker_load_ms\":"+std::to_string(load_ms)+
      ",\"callback_ttft_ms\":"+std::to_string(callback_first)+
      ",\"request_total_ms\":"+std::to_string(elapsed(at))+",\"threads\":"+std::to_string(threads)+"}";
    std::cout<<"\nBT1 STATS "<<stats.size()<<"\n"<<stats<<"\n";
    bool ok=error==executorch::runtime::Error::Ok;
    std::string payload=ok?generated:"ExecuTorch generation failed";
    std::cout<<"BT1 "<<(ok?"OK":"ERROR")<<" "<<payload.size()<<"\n"<<payload<<"\n"<<std::flush;
  }
}
