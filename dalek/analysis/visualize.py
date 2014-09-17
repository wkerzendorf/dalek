import pandas as pd

from dalek import triangle
from dalek.parallel import ParameterCollection
from tardis.io.config_reader import ConfigurationNameSpace

def simple_triangle_plot(dalek_log_file, truth_config=None, plot_contours=False):
    """

    Parameters
    ----------

    dalek_log_file : ~str
        path to normal dalek log file
    truth_config : ~str
        path to tardis config file containing the truth values [optional]

    plot_contours : ~bool
        plotting contours for the distributions

    :return:
    """
    dalek_data = pd.read_csv(dalek_log_file, index_col=0)
    if truth_config is not None:
        truth_config = ConfigurationNameSpace.from_yaml(truth_config)

    data_columns = [item for item in dalek_data.columns if not item.startswith('dalek.')]
    abundance_columns = [item for item in data_columns if 'abundance' in item]
    fitness = dalek_data['dalek.fitness']
    labels = []
    truths = []
    for column in dalek_data.columns:
        if 'dalek' in column:
            continue
        if column.endswith('item0'):
            label = '.'.join(column.split('.')[-2:])
        else:
            label = column.split('.')[-1]

        labels.append(label)

        if truth_config is not None:
            default_value = truth_config.get_config_item(column)
            default_value = getattr(default_value, 'value', default_value)
            truths.append(default_value)

    if truths == []:
        truths = None

    dalek_data[abundance_columns] = dalek_data[abundance_columns].values / dalek_data[abundance_columns].sum(axis=1).values[None].T

    triangle.corner(dalek_data[data_columns], weights=1/fitness,
                    labels=labels,
                    plot_contours=plot_contours, normed=True, truths=truths)



