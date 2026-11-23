// Project worker for the pinned ExecuTorch v1.0.0 public C++ runner API.
// One model load, independent requests with KV reset; no network dependencies.
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>
#include <executorch/examples/models/llama/runner/runner.h>
#if defined(ET_USE_THREADPOOL)
#include <executorch/extension/threadpool/threadpool.h>
#endif

int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "Usage: blistertrace_worker MODEL.pte tokenizer.model THREADS\n";
    return 2;
  }
  const int threads = std::atoi(argv[3]);
  if (threads < 1 || threads > 4) return 2;
#if defined(ET_USE_THREADPOOL)
  executorch::extension::threadpool::get_threadpool()->_unsafe_reset_threadpool(threads);
#endif
  auto runner = example::create_llama_runner(argv[1], argv[2], std::vector<std::string>{});
  if (!runner || runner->load() != executorch::runtime::Error::Ok) return 3;
  std::cout << "BT1 READY 0\n" << std::flush;
  std::string magic;
  size_t size;
  int max_new;
  while (std::cin >> magic >> size >> max_new) {
    if (magic != "BT1" || size == 0 || size > 32768 || max_new < 1 || max_new > 256) return 4;
    if (std::cin.get() != '\n') return 4;
    std::string prompt(size, '\0');
    if (!std::cin.read(prompt.data(), size)) return 4;
    std::string generated;
    runner->reset();
    executorch::extension::llm::GenerationConfig config;
    config.echo = false;
    config.max_new_tokens = max_new;
    config.seq_len = 1024;
    config.temperature = 0.0f;
    auto error = runner->generate(prompt, config, [&](const std::string& token) {
      generated += token;
      if (generated.size() > 8192) runner->stop();
    });
    const bool ok = error == executorch::runtime::Error::Ok;
    const std::string payload = ok ? generated : "ExecuTorch generation failed";
    // Upstream may print performance statistics on stdout. The client skips
    // non-protocol lines and reads precisely the payload's byte count.
    std::cout << "\nBT1 " << (ok ? "OK" : "ERROR") << " " << payload.size() << "\n";
    std::cout.write(payload.data(), payload.size());
    std::cout << "\n" << std::flush;
  }
  return 0;
}
