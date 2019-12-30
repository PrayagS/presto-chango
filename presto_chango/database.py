import os
import random
from presto_chango.song import song_recipe, convert_to_wav
import pickle
import scipy.io.wavfile as wavfile


def hash_window(filtered_bin):
    """
    :param filtered_bin: A filtered bin of a window generated by filter_spectrogram
    :return: hash value of the particular bin
    """
    """
    Note that we must assume that the recording is not done in perfect conditions (i.e., a “deaf room”),
    and as a result we must include a fuzz factor.
    Fuzz factor analysis should be taken seriously, and in a real system,
    the program should have an option to set this parameter based on the conditions of the recording.
    """
    fuz_factor = 2  # for error correction
    return (filtered_bin[3] - (filtered_bin[3] % fuz_factor)) * 1e8 + (
        filtered_bin[2] - (filtered_bin[2] % fuz_factor)) * 1e5 + (
        filtered_bin[1] - (filtered_bin[1] % fuz_factor)) * 1e2 + (
        filtered_bin[0] - (filtered_bin[0] % fuz_factor))


def hash_song(song_id, filtered_bins, hash_dictionary):
    """
    Modifies hash_dictionary to map data of the given song_id
    :param song_id: id of the particular song
    :param filtered_bins: bins generated by song_recipe
    :param hash_dictionary
    """
    for i, filtered_bin in enumerate(filtered_bins):
        try:
            hash_dictionary[hash_window(filtered_bin)].append((song_id, i))
        except KeyError:
            hash_dictionary[hash_window(filtered_bin)] = [(song_id, i)]


def hash_sample(filtered_bins):
    """
    Create a HashMap of the filtered bins
    :param filtered_bins:
    :return sample_dictionary:
    """
    sample_dictionary = {}
    for i, filtered_bin in enumerate(filtered_bins):
        try:
            sample_dictionary[hash_window(filtered_bin)].append(i)
        except KeyError:
            sample_dictionary[hash_window(filtered_bin)] = [i]
    return sample_dictionary


def create_database(song_dir):
    """
    :return: song_to_id - Maps song names to generated ids, id_to_song - Maps ids to song
    hash_dictionary - Maps hash values to associated song ids and offset values
    """
    if os.path.exists('Songs'):
        pass
    else:
        os.mkdir('Songs')
    song_to_id = {}
    id_to_song = {}
    hash_dictionary = {}
    random_ids = random.sample(range(1000), len(os.listdir(song_dir)))
    for song_id, filename in zip(random_ids, os.listdir(song_dir)):
        print(filename)
        song_to_id[filename] = song_id
        id_to_song[song_id] = filename
        filtered_bins = song_recipe(os.path.join(song_dir, filename))
        hash_song(song_id, filtered_bins, hash_dictionary)
    with open('Songs.pickle', 'wb') as f:  # Object serialization
        pickle.dump(song_to_id, f)
        pickle.dump(id_to_song, f)
        pickle.dump(hash_dictionary, f)
    print('\nDatabase created successfully!')
    return song_to_id, id_to_song, hash_dictionary


def load_database():
    """
    Load data stored in a serialized file
    :return song_to_id, id_to_song, hash_dictionary:
    """
    with open('Songs.pickle', 'rb') as f:  # Load data from a binary file
        song_to_id = pickle.load(f)
        id_to_song = pickle.load(f)
        hash_dictionary = pickle.load(f)
    return song_to_id, id_to_song, hash_dictionary


def find_song(hash_dictionary, sample_dictionary, id_to_song):
    """
    Run our song matching algorithm to find the song
    :param hash_dictionary:
    :param sample_dictionary:
    :param id_to_song:
    :return max_frequencies, max_frequencies_keys:
    """
    offset_dictionary = dict()
    for song_id in id_to_song.keys():
        offset_dictionary[song_id] = {}
    song_size = {}
    for song_id in id_to_song.keys():
        rate, data = wavfile.read(os.path.join("Songs", id_to_song[song_id]))
        song_size[song_id] = len(data) / rate
    for sample_hash_value, sample_offsets in sample_dictionary.items():
        for sample_offset in sample_offsets:
            try:
                for song_id, offset in hash_dictionary[sample_hash_value]:
                    try:
                        offset_dictionary[song_id][(
                            offset - sample_offset) // 1] += 1
                    except KeyError:
                        offset_dictionary[song_id][(
                            offset - sample_offset) // 1] = 1
            except KeyError:
                pass
    max_frequencies = {}
    for song_id, offset_dict in offset_dictionary.items():
        for relative_set, frequency in offset_dict.items():
            try:
                max_frequencies[song_id] = max(
                    max_frequencies[song_id], frequency)
            except KeyError:
                max_frequencies[song_id] = frequency
    max_frequencies_keys = sorted(
        max_frequencies, key=max_frequencies.get, reverse=True)
    return max_frequencies, max_frequencies_keys


def batch_convert_to_wav():
    """
    Batch convert files to WAV for database purposes
    :return:
    """
    mp3_dir = "MP3 Songs"
    for filename in os.listdir(mp3_dir):
        convert_to_wav(os.path.join(mp3_dir, filename), "Songs")


if __name__ == "__main__":
    create_database()
