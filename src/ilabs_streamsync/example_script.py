from __future__ import annotations

import mne
from streamsync import StreamSync, extract_audio_from_video

if __name__ == "__main__":
    # load an MNE raw file
    raw = "/Users/user/VideoSync_NonSubject/sinclair_alexis_audiosync_240110_raw.fif"
    channel = "STI011"
    cams = ["/Users/user/VideoSync_NonSubject/sinclair_alexis_audiosync_240110_CAM3.mp4"]
    output_dir = "/Users/user/VideoSync_NonSubject/output"
    flux1 = None
    my_events = []

    for cam in cams:
        extract_audio_from_video(cam, output_dir, overwrite=False) #This could potentially return filenames to avoid the hardcoding seen below.
    ss = StreamSync(raw, channel)

    ss.add_stream("/Users/user/VideoSync_NonSubject/output/sinclair_alexis_audiosync_240110_CAM3_16bit.wav", channel=1)
    ss.plot_sync_pulses(tmin=0.5,tmax=50)

    # subjects = ["146a", "222b"]

    # for subj in subjects:
        # construct the filename/path
        # load the Raw
        # figure out where video files are & load them
        # extract_audio_from_video(cam1)

        # ss = StreamSync(raw, "STIM001")
        # ss.add_stream(audio1)
        # ss.add_camera_events(my_events)
        # ss.add_stream(flux1)
        # result = ss.do_syncing()
        # fig = ss.plot_sync()
        # annot = ss.add_camera_events(my_events)
        # raw.set_annotations(annot)
        # fig.savefig(...)
        # if result < 0.7:
        #     write_log_msg(f"subj {subj} had bad pulse syncing, aborting")
        #     continue

        # apply maxfilter
        # do ICA
