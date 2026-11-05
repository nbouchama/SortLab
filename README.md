SortLab is an educational sorting visualizer built with Python and Tkinter. It animates sorting operations on a bar chart and explains each step through a detailed log. Compare algorithms using custom data, track their operations, and explore how input patterns affect performance.


Features
- Visualize sorting step by step: Start, pause, resume, advance one operation at a time, or move back to a previous step.
- Explore 11 algorithms: Bubble sort, optimized bubble sort, selection sort, insertion sort, Shell sort, quicksort, merge sort, cocktail sort, heapsort, counting sort, and radix sort.
- Try different input patterns: Generate random, sorted, reverse-sorted, nearly sorted, duplicate-heavy, low-variety, or negative-valued datasets.
- Use custom data: Enter your own integer values or reorder the bars by dragging them.
- Compare algorithm properties: Review best, average, and worst-case complexity, stability, and in-place behavior alongside measured comparisons, writes, swaps, and elapsed time.
- Run side-by-side races: Animate two algorithms on the same dataset.
- Study complexity growth: Benchmark an algorithm at multiple input sizes and compare measured results with O(n), O(n log n), and O(n²) reference curves.
- Practise with challenges: Choose the algorithm that makes the fewest comparisons for a given dataset.
- Save and share experiments: Store datasets and settings as JSON files; export comparison reports to CSV.
- Use a conventional desktop interface: Navigate between simulation, statistics, comparisons, complexity, challenges, and help.


Requirements
- Python 3.8 or later
- Tkinter, usually included with standard Python distributions


Run
python SortLab.py
