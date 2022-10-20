import os
from shutil import copyfile
import hashlib
from concurrent.futures import ThreadPoolExecutor
c = 0
def get_sha1(file_path):
    hasher = hashlib.sha1()
    try:
        with open(file_path, 'rb') as afile:
            buf = afile.read()
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read()
    except:
        return None
    copy_pdfs(file_path, hasher.hexdigest())


def copy_pdfs(file, doi):
    try:
        c += 1
        print(c)
        if (c%100 == 0):
            with open('count_repo_progress.txt', 'w') as cfile:
                cfile.write(str(c))
        chunks = [doi[i : i + 2] for i in range(0, len(doi), 2)]
        filename = doi + ".pdf"
        pdf_repo_path = os.path.join('/mnt/csxrepo01_repo/csx_beta_repo/', chunks[0], chunks[1], chunks[2], chunks[3], chunks[4], chunks[5],
                                        chunks[6], doi, filename)
        if (not os.path.exists(pdf_repo_path)):
            os.makedirs(os.path.dirname(pdf_repo_path), exist_ok=True)
            copyfile(src=file, dst=pdf_repo_path)
    except Exception:
        pass

if __name__ == '__main__':
    import glob
    file_list =  list(glob.iglob('/mnt/rep1/**/*.pdf', recursive=True))

    file_list = file_list[2000000:]
    with ThreadPoolExecutor(50) as executor:
        # download each url and save as a local file
        _ = [executor.submit(get_sha1, file) for file in file_list]