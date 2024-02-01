# Copyright (c) 2024 Carbonyl LLC & Carbonyl R&D
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import os


class GenieLoader():

    @staticmethod
    def estimate_optimal_npartitions(data, partition_size_limit=1e6):
        """
        Estimate the optimal number of partitions for a dask DataFrame based on dataset size,
        available memory and number of cores.

        :param data: pandas DataFrame or Series
        :param partition_size_limit: Maximum number of rows for each partition. Default is 1e6.
        :return: Estimated optimal number of partitions
        """
        import psutil
        # Calculate total memory (RAM) in bytes
        total_mem = psutil.virtual_memory().total

        # Calculate the size of the dataset in bytes
        data_size = data.memory_usage(index=True, deep=True).sum()

        # Get the number of cores
        num_cores = os.cpu_count()

        # Estimate the number of partitions based on data size
        npartitions_data_size = int(data_size / partition_size_limit)

        # Estimate the number of partitions based on total memory and data size
        npartitions_mem = int(total_mem / data_size) if data_size != 0 else num_cores

        # Choose the minimum value among the three estimates
        npartitions = min(num_cores, npartitions_data_size, npartitions_mem)

        # Ensure npartitions is at least 1
        npartitions = max(1, npartitions)

        return npartitions

    def find_file(self, file_name, data_file_dirs: list or tuple):

        for directory in data_file_dirs:
            if os.path.isfile(f'{directory}/{file_name}'):
                return directory
        raise FileNotFoundError(f'Could not find {file_name} in {data_file_dirs}')

    def fetch_csv_data_dask(self, data_file_name, data_file_dir, scheduler='threads',
                            n_rows=None, first_or_last='first'):
        import dask.dataframe as dd
        data_file_path = f'{data_file_dir}/{data_file_name}'
        bar_data = dd.read_csv(data_file_path, parse_dates=False)

        if n_rows:
            if first_or_last == 'first':
                bar_data = dd.read_csv(data_file_path, parse_dates=True, sample=100000000).head(n_rows)
            elif first_or_last == 'last':
                bar_data = dd.read_csv(data_file_path, parse_dates=True, sample=100000000).tail(n_rows)
        else:
            bar_data = dd.read_csv(data_file_path, parse_dates=True, sample=100000000)

        # parse the datetime column
        datetime_col = bar_data.columns[0]
        bar_data[datetime_col] = dd.to_datetime(bar_data[datetime_col])
        # bar_data[datetime_col] = bar_data[datetime_col].dt.strftime(output_format)
        if not n_rows:
            # compute the dask dataframe
            bar_data = bar_data.compute(scheduler=scheduler)

        # set the datetime column as the index
        bar_data.index = bar_data[datetime_col]
        # delete the datetime column
        del bar_data[datetime_col]
        return bar_data

    @staticmethod
    def combine_csv_files_dask(
            file_paths: str,
            save_path: str,
            save: bool = True,
            remove_duplicates: bool = True,
            dtype: dict = None,
            **kwargs,
    ):
        """
        Load and row combine all csv files inside Reports folder and save them into a large csv file. Preferably,
        this should be done in parallel and using dask since the csv files are large.
        """
        from dask import dataframe as dd
        from glob import glob
        # Get the list of csv files
        csv_files = glob(file_paths)

        # Read the csv files in parallel
        df = dd.read_csv(csv_files, dtype=dtype, **kwargs)
        # Combine the dataframes
        df = df.compute()

        # What is the length of the dataframe?

        if save:
            # Save the dataframe
            df.to_csv(save_path, index=False, **kwargs)

        if remove_duplicates:
            # Remove duplicates
            df.drop_duplicates(inplace=True)
        return df

    def fetch(self, data_file_names, data_file_dirs, **kwargs):
        return self.fetch_data(data_file_names, data_file_dirs, **kwargs)

