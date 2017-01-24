FROM fliem/lhab_pipelines_base:v1.0

# tools that are in dev

RUN npm install -g bids-validator@0.19.8


#### DCM2NIIX
WORKDIR /root
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y build-essential pkg-config libyaml-cpp-dev libyaml-cpp0.5 cmake libboost-dev git pigz unzip && \
	  apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y

RUN cd /tmp && \
    wget https://github.com/rordenlab/dcm2niix/archive/d7ab348bf95b398222d4053646d6c2ee11a73449.zip -O dcm2niix.zip && \
    unzip dcm2niix.zip && rm dcm2niix.zip && \
  	cd dcm2niix-* && cmake -DCMAKE_INSTALL_PREFIX:PATH=/usr/ . && make install && \
    cd /tmp && rm -rf /tmp/dcm2niix*



RUN pip install pybids

COPY lhab_pipelines /code/lhab_pipelines/lhab_pipelines
COPY scripts /code/lhab_pipelines/scripts
COPY version /code/lhab_pipelines/version
ENV PYTHONPATH=/code/lhab_pipelines:$PYTHONPATH

CMD ["/bin/bash"]
