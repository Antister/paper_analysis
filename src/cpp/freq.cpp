#include <algorithm>
#include <cctype>
#include <cstddef>
#include <cstdint>
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

#include "paper.hpp"
#include "words.hpp"


/* Word frequency to return */
using result_t = std::unordered_map<int /*year*/, std::unordered_map<std::string /*word*/, double /*freq*/>>;

result_t compute_word_freq(const std::vector<paper_t> &papers, const std::vector<int> &years, std::size_t task_count)
{
    if (!(papers.size() && years.size() && task_count))
        return {};

    auto local_years = years;
    std::ranges::sort(local_years);

    /* Data structure for parallel, each year a lock */
    struct parallel_data_t
    {
        std::mutex year_lock;

        std::size_t year_paper_count;
        std::unordered_map<std::string /*word*/, std::int64_t /*count*/> freq_map;
    };
    std::unordered_map<int /*year*/, parallel_data_t> year_freq_map{};
    for (auto i : years)
        year_freq_map[i]; // Preinitialize to prevent parallel construct

    /* Task function to process a chunk of data  */
    auto task = [&](const std::ranges::viewable_range auto &part)
    {
        for (const auto &paper : part)
        {
            // Check whether the paper's year is valid
            auto year = std::get<1>(paper);
            if (year < local_years[0] || year > local_years.back())
                continue;

            // Preprocess the title: to lower, keep alnum and '-'
            const std::string &str = std::get<2>(paper);
            std::string washed_str{};
            washed_str.reserve(str.size());
            for (auto ch : str)
                if (std::isalnum(ch) || std::isspace(ch) || ch == '-') [[likely]]
                    washed_str.push_back(std::tolower(ch));

            // Tokenize the title
            std::vector<std::string> tokens{};
            auto raw_tokens = washed_str | std::views::split(' ') |
                              std::views::filter([](auto &&r) { return std::ranges::size(r) > 0; }) |
                              std::views::transform([](auto &&r) { return std::string_view{r}; }) |
                              std::ranges::to<std::vector>();
            for (std::size_t i = 0; i < raw_tokens.size();) // Try to match terminologies in title
            {
                bool is_match_success = false;

                for (auto count = TERMINOLOGY_MIN_WORDS;
                     count <= std::min(raw_tokens.size() - i, TERMINOLOGY_MAX_WORDS);
                     ++count) // Tranverse each space-splited token and check whether they can from a terminology
                {
                    auto token_str = std::views::counted(raw_tokens.begin() + i, count) | std::views::join_with(' ') |
                                     std::ranges::to<std::string>();
                    if (TERMINOLOGY.contains(std::string_view{token_str}))
                    {
                        tokens.emplace_back(std::move(token_str));
                        i += count;
                        is_match_success = true;
                    }
                }

                if (!is_match_success) // Otherwise, add the token to count if it is not a stop word
                {
                    if (!STOPWORDS.contains(raw_tokens[i]))
                        tokens.emplace_back(raw_tokens[i]);
                    ++i;
                }
            }

            auto &&freq_table = year_freq_map[year];
            std::lock_guard guard{freq_table.year_lock}; // Acquire year-lock to modify shared data
            for (const auto &s : tokens)
                freq_table.freq_map[s]++;
            freq_table.year_paper_count += tokens.size();
        }
    };

    {
        std::vector<std::jthread> tasks{};
        for (const auto partition : papers | std::views::chunk(papers.size() / task_count))
            tasks.emplace_back(task, partition);
    }

    /* Convert count to frequency */
    result_t result{};
    for (auto &[year, result_data] : year_freq_map)
        for (auto &[word, count] : result_data.freq_map)
            if (auto freq = count / double(result_data.year_paper_count); freq > 1e-3)
                result[year][word] = freq;

    return result;
}

/* Bind the function above to python */
NB_MODULE(freq, mod)
{
    mod.def("compute_word_freq", compute_word_freq, "Compute word frequencies by year");
}