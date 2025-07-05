#include <algorithm>
#include <cctype>
#include <cstddef>
#include <mutex>
#include <ranges>
#include <string_view>
#include <thread>
#include <utility>

#include <nanobind/nanobind.h>

#include <nanobind/stl/string.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/unordered_map.h>
#include <nanobind/stl/vector.h>

#include "words.hpp"

using paper_t = std::tuple</*conference*/ std::string,
                           /*year*/ int,
                           /*title*/ std::string,
                           /*authors*/ std::vector<std::string>,
                           /*url*/ std::string>;
using result_t = std::unordered_map</*year*/ int,
                                    std::unordered_map<
                                        /*word*/ std::string,
                                        /*freq*/ double>>;

result_t compute_word_freq(const std::vector<paper_t> &papers, const std::vector<int> &years, std::size_t task_count)
{
    if (!(papers.size() && years.size() && task_count))
        return {};

    auto local_years = years;
    std::ranges::sort(local_years);

    struct parallel_data_t
    {
        std::mutex lock;

        std::size_t year_paper_count;
        std::unordered_map<
            /*word*/ std::string,
            /*count*/ double>
            data;
    };
    std::unordered_map</*year*/ int, parallel_data_t> temp_data{};
    for (auto i : years)
        temp_data[i];

    auto task = [&](const std::ranges::viewable_range auto &part)
    {
        for (const auto &paper : part)
        {
            auto year = std::get<1>(paper);
            if (year < local_years[0] || year > local_years.back())
                continue;

            const std::string &str = std::get<2>(paper);
            std::string washed_str{};
            washed_str.reserve(str.size());
            for (auto ch : str)
                if (std::isalnum(ch) || std::isspace(ch) || ch == '-') [[likely]]
                    washed_str.push_back(std::tolower(ch));

            std::vector<std::string_view> tokens{};
            for (auto tk : washed_str | std::views::split(' '))
                if (!STOPWORDS.contains(std::string_view{tk}))
                    tokens.emplace_back(tk);

            auto &&freq_table = temp_data[year];
            std::lock_guard guard{freq_table.lock};
            for (auto &s : tokens)
                freq_table.data[std::string{s}] += 1.0;
            freq_table.year_paper_count += tokens.size();
        }
    };

    {
        std::vector<std::jthread> tasks{};
        for (const auto partition : papers | std::views::chunk(task_count))
            tasks.emplace_back(task, partition);
    }

    result_t result{};
    for (auto &[year, result_data] : temp_data)
        for (auto &[word, count] : result_data.data)
            if (auto freq = count / result_data.year_paper_count; freq > 1e-3)
                result[year][word] = freq;

    return result;
}

NB_MODULE(freq, mod)
{
    mod.def("compute_word_freq", compute_word_freq, "Compute word frequencies by year");
}