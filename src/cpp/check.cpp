#include <cstddef>
#include <mutex>
#include <ranges>
#include <span>
#include <thread>

#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>

#include "paper.hpp"

using invalid_paper_t = std::vector<std::size_t /* index */>;

invalid_paper_t validate_html_data(const std::vector<paper_t> &html_data,
                                   const std::vector<paper_t> &xml_data,
                                   std::size_t task_count)
{
    invalid_paper_t result{};
    std::mutex lock{};

    auto task = [&](const std::span<const paper_t> html_part)
    {
        invalid_paper_t mismatch_papers{};
        bool is_match = false;

        for (const auto html_idx : std::views::iota(0u, html_part.size()))
        {
            for (const auto &xml_paper : xml_data)
            {
                if (std::get<2>(html_part[html_idx]) == std::get<2>(xml_paper)) [[unlikely]]
                {
                    is_match = true;
                    break;
                }
            }

            if (is_match)
                is_match = false;
            else
                mismatch_papers.emplace_back(html_part.data() - html_data.data() + html_idx);
        }

        std::lock_guard guard{lock};
        result.append_range(std::move(mismatch_papers));
    };

    {
        std::vector<std::jthread> tasks{};
        for (const auto partition : html_data | std::views::chunk(html_data.size() / task_count))
            tasks.emplace_back(task, partition);
    }

    return result;
}

/* Bind the function above to python */
NB_MODULE(check, mod)
{
    mod.def("validate_html_data", validate_html_data, "Check whether the data from HTML match the which from XML");
}