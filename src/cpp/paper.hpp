#include <nanobind/stl/string.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/vector.h>

/* Represent a paper */
using paper_t = std::tuple<std::string /*conference*/,
                           int /*year*/,
                           std::string /*title*/,
                           std::vector<std::string> /*authors*/,
                           std::string /*url*/>;