require 'json'

TOOLS_DIR = File.expand_path('tools')
NODE_VER = 'node-v10.16.3-linux-x64'
ENV['PATH'] = "#{TOOLS_DIR}/#{NODE_VER}/bin:#{ENV['PATH']}"
NPX = "#{TOOLS_DIR}/#{NODE_VER}/bin/npx"
NG = File.expand_path('webui/node_modules/.bin/ng')
SWAGGER_CODEGEN = "#{TOOLS_DIR}/swagger-codegen-cli-2.4.8.jar"
SWAGGER_FILE = File.expand_path("server/kraken/server/swagger.yml")

kk_ver = ENV['kk_ver'] || '0.0'
ENV['KRAKEN_VERSION'] = kk_ver
KRAKEN_VERSION_FILE = File.expand_path("kraken-version-#{kk_ver}.txt")

# prepare env
task :prepare_env do
  sh 'sudo DEBIAN_FRONTEND=noninteractive apt-get install -y default-jre python3-venv npm libpq-dev libpython3.7-dev'
  sh 'python3 -m venv venv && ./venv/bin/pip install -U pip'
end

# UI
task :gen_client => [SWAGGER_CODEGEN, SWAGGER_FILE] do
  Dir.chdir('ui') do
    sh "java -jar #{SWAGGER_CODEGEN} generate  -l typescript-angular -i #{SWAGGER_FILE} -o src/app/backend --additional-properties snapshot=true,ngVersion=8.2.8,modelPropertyNaming=snake_case"
  end
end

file SWAGGER_CODEGEN do
  sh "mkdir -p #{TOOLS_DIR}"
  sh "wget http://central.maven.org/maven2/io/swagger/swagger-codegen-cli/2.4.8/swagger-codegen-cli-2.4.8.jar -O #{SWAGGER_CODEGEN}"
end

file NPX do
  sh "mkdir -p #{TOOLS_DIR}"
  Dir.chdir(TOOLS_DIR) do
    sh "wget https://nodejs.org/dist/v10.16.3/#{NODE_VER}.tar.xz -O #{TOOLS_DIR}/node.tar.xz"
    sh "tar -Jxf node.tar.xz"
  end
end

file NG => NPX do
  Dir.chdir('ui') do
    sh 'npm install'
  end
end

task :build_ui => [NG, :gen_client] do
  Dir.chdir('ui') do
    sh "sed -e 's/0\.0/#{kk_ver}/g' src/environments/environment.prod.ts.in > src/environments/environment.prod.ts"
    sh 'npx ng build --prod'
  end
end

task :serve_ui => [NG, :gen_client] do
  Dir.chdir('ui') do
    sh 'npx ng serve --host 0.0.0.0 --disable-host-check --proxy-config proxy.conf.json'
  end
end

task :lint_ui => [NG, :gen_client] do
  Dir.chdir('ui') do
    sh 'npm ci'
    sh 'npx ng lint'
    sh 'npx prettier --config .prettierrc --check \'**/*\''
  end
end

task :fix_ui => [NG, :gen_client] do
  Dir.chdir('ui') do
    sh 'npx ng lint --fix'
    sh 'npx prettier --config .prettierrc --write \'**/*\''
  end
end


# BACKEND

file './venv/bin/python3' do
  sh 'python3 -m venv venv'
  sh './venv/bin/pip install -U pip'
end

file './server/venv/bin/python3' do
  sh 'python3 -m venv server/venv'
  sh './server/venv/bin/pip install -U pip'
end

file './agent/venv/bin/python3' do
  sh 'python3 -m venv agent/venv'
  sh './agent/venv/bin/pip install -U pip'
end

def setup_py_develop
  Dir.chdir('server') do
    sh './venv/bin/pip install -r requirements.txt'
    sh './venv/bin/python3 setup.py develop --upgrade'
  end
end

file KRAKEN_VERSION_FILE do
  sh 'rm -f kraken-version-*.txt'
  sh "touch #{KRAKEN_VERSION_FILE}"
end

file 'server/kraken/version.py' => KRAKEN_VERSION_FILE do
  sh "echo \"version = '#{kk_ver}'\" > server/kraken/version.py"
end

task :run_server => 'server/kraken/version.py' do
  Dir.chdir('server') do
    sh 'KRAKEN_LOGSTASH_ADDR=192.168.0.88:5959 KRAKEN_STORAGE_ADDR=192.168.0.88:2121 ../venv/bin/poetry run kkplanner'
  end
end

task :run_scheduler => 'server/kraken/version.py' do
  Dir.chdir('server') do
    sh '../venv/bin/poetry run kkscheduler'
  end
end

file './agent/venv/bin/kkagent' => './agent/venv/bin/python3' do
  Dir.chdir('agent') do
    sh './venv/bin/pip install -r requirements.txt'
    sh './venv/bin/python3 setup.py develop --upgrade'
  end
end

task :run_agent => './agent/venv/bin/kkagent' do
  sh 'cp server/kraken/server/consts.py agent/kraken/agent/'
  sh 'cp server/kraken/server/logs.py agent/kraken/agent/'
  sh 'rm -rf /tmp/kk-jobs/'
  sh 'bash -c "source ./agent/venv/bin/activate && kkagent -d /tmp/kk-jobs -s http://localhost:8080 run"'
end

task :run_agent_in_docker do
  Rake::Task["build_agent"].invoke
  Dir.chdir('agent') do
    sh 'docker build -f docker-agent.txt -t kkagent .'
  end
  sh 'docker run --rm -ti  -v /var/run/docker.sock:/var/run/docker.sock -v /var/snap/lxd/common/lxd/unix.socket:/var/snap/lxd/common/lxd/unix.socket -v `pwd`/agent:/agent -e KRAKEN_AGENT_SLOT=7 -e KRAKEN_SERVER_ADDR=192.168.0.89:8080  kkagent'
end

task :run_agent_in_lxd do
#  Rake::Task["build_agent"].invoke
  Dir.chdir('agent') do
    systems = [
      ['ubuntu:20.04', 'u20'],
      ['images:fedora/32/amd64', 'f32'],
#      ['images:centos/7/amd64', 'c7'],
      ['images:centos/8/amd64', 'c8'],
      ['images:debian/buster/amd64', 'd10'],
      ['images:debian/bullseye/amd64', 'd11'],
      ['images:opensuse/15.2/amd64', 's15'],
    ]

    sh 'lxc network delete kk-net || true'
    sh 'lxc network create kk-net || true'
    systems.each do |sys, name|
      cntr_name = "kk-agent-#{name}"
      sh "lxc stop #{cntr_name} || true"
      sh "lxc delete #{cntr_name} || true"
      sh "lxc launch #{sys} #{cntr_name}"
      sh "lxc network attach kk-net #{cntr_name}"
      sh "lxc exec #{cntr_name} -- sleep 5"
      if sys.include?('centos/7') or sys.include?('debian/buster')
        sh "lxc exec #{cntr_name} -- dhclient"
      end
      if sys.include?('centos')
        sh "lxc exec #{cntr_name} -- yum install -y python3 sudo"
      end
      if sys.include?('debian')
        sh "lxc exec #{cntr_name} -- apt-get update"
        sh "lxc exec #{cntr_name} -- apt-get install -y curl python3 sudo"
      end
      if sys.include?('opensuse/15.2')
        sh "lxc exec #{cntr_name} -- zypper install -y curl python3 sudo system-group-wheel"
      end
      sh "lxc exec #{cntr_name} -- curl -o agent http://192.168.0.89:8080/install/agent"
      sh "lxc exec #{cntr_name} -- chmod a+x agent"
      sh "lxc exec #{cntr_name} -- ./agent -s http://192.168.0.89:8080 install"
      sh "lxc exec #{cntr_name} -- journalctl -u kraken-agent.service"
      #sh "lxc exec #{cntr_name} -- journalctl -f -u kraken-agent.service'
    end
  end
end

task :run_celery => './server/venv/bin/kkcelery' do
  sh './server/venv/bin/kkcelery'
end

task :run_planner => 'server/kraken/version.py' do
  Dir.chdir('server') do
    sh '../venv/bin/poetry run kkplanner'
  end
end

task :run_watchdog => 'server/kraken/version.py' do
  Dir.chdir('server') do
    sh '../venv/bin/poetry run kkwatchdog'
  end
end

task :run_storage => 'server/kraken/version.py' do
  Dir.chdir('server') do
    sh '../venv/bin/poetry run kkstorage'
  end
end

file './venv/bin/shiv' => ['./venv/bin/python3', 'requirements.txt'] do
    sh './venv/bin/pip install -r requirements.txt'
end

task :build_agent => './venv/bin/shiv' do
  sh 'cp server/kraken/server/consts.py agent/kraken/agent/'
  sh 'cp server/kraken/server/logs.py agent/kraken/agent/'
  Dir.chdir('agent') do
    sh 'rm -rf dist-agent'
    sh '../venv/bin/pip install --target dist-agent -r requirements.txt'
    sh '../venv/bin/pip install --target dist-agent --upgrade .'
    sh "../venv/bin/shiv --site-packages dist-agent --compressed -p '/usr/bin/env python3' -o kkagent -c kkagent"
    sh 'rm -rf dist-tool'
    sh '../venv/bin/pip install --target dist-tool --upgrade .'
    sh "../venv/bin/shiv --site-packages dist-tool --compressed -p '/usr/bin/env python3' -o kktool -c kktool"
  end
  sh "cp agent/kkagent agent/kktool server/"
end

task :build_py => [:build_agent]

task :clean_backend do
  sh 'rm -rf venv'
  sh 'rm -rf server/venv'
  sh 'rm -rf agent/venv'
end

task :build_all => [:build_py, :build_ui]

# when there is storage limit hit in ELK then do this
task :unlock_elk do
  sh 'curl -XPUT -H "Content-Type: application/json" http://localhost:9200/_cluster/settings -d \'{ "transient": { "cluster.routing.allocation.disk.threshold_enabled": false } }\''
  sh 'curl -XPUT -H "Content-Type: application/json" http://localhost:9200/_all/_settings -d \'{"index.blocks.read_only_allow_delete": null}\''
end

# DATABASE
DB_URL = "postgresql://kraken:kk123@localhost:5433/kraken"
task :db_up do
  Dir.chdir('server/migrations') do
    sh "KRAKEN_DB_URL=#{DB_URL} ../venv/bin/alembic -c alembic.ini upgrade head"
  end
end

task :db_down do
  Dir.chdir('server/migrations') do
    sh "KRAKEN_DB_URL=#{DB_URL} ../venv/bin/alembic -c alembic.ini downgrade -1"
  end
end

task :db_init do
  Dir.chdir('server/migrations') do
    sh "KRAKEN_DB_URL=#{DB_URL} ../venv/bin/python3 apply.py"
  end
end


# DOCKER

task :docker_up => :build_all do
#task :docker_up do
  sh "docker-compose down"
  sh "docker-compose build --build-arg kkver=#{kk_ver}"
  sh "docker-compose up"
end

task :docker_down do
  sh "docker-compose down -v"
end

task :run_elk do
  sh 'docker-compose up kibana logstash elasticsearch'
end

task :run_pgsql do
  sh 'docker run --rm -p 5433:5432 -e POSTGRES_USER=kraken -e POSTGRES_PASSWORD=kk123 -e POSTGRES_DB=kraken postgres:11'
end

task :run_redis do
  sh 'docker run --rm -p 6379:6379 redis:alpine'
end

task :build_docker_deploy do
  sh 'docker-compose -f docker-compose-swarm.yaml config > docker-compose-swarm-deploy.yaml'
end

task :docker_release do
  # for lab.kraken.ci
  sh "docker-compose -f docker-compose-swarm.yaml config > kraken-docker-stack-#{kk_ver}.yaml"
  sh "sed -i -e s/kk_ver/#{kk_ver}/g kraken-docker-stack-#{kk_ver}.yaml"
  # for installing under the desk and for pushing images to docker images repository
  sh "docker-compose -f docker-compose.yaml config > kraken-docker-compose-#{kk_ver}-tmp.yaml"
  sh "sed -i -e s/kk_ver/#{kk_ver}/g kraken-docker-compose-#{kk_ver}-tmp.yaml"
  sh "sed -i -e 's#127.0.0.1:5000#eu.gcr.io/kraken-261806#g' kraken-docker-compose-#{kk_ver}-tmp.yaml"
  sh "cp agent/kkagent agent/kktool server/"
  sh "docker-compose -f kraken-docker-compose-#{kk_ver}-tmp.yaml build --force-rm --no-cache --pull --build-arg kkver=#{kk_ver}"
  sh "docker-compose -f kraken-docker-compose-#{kk_ver}-tmp.yaml push"
  sh "cat kraken-docker-compose-#{kk_ver}-tmp.yaml | grep -v 'context:' | grep -v 'dockerfile:'| grep -v 'build:' > kraken-docker-compose-#{kk_ver}.yaml"
  sh "rm kraken-docker-compose-#{kk_ver}-tmp.yaml"
end

task :prepare_swarm do
  sh 'sudo DEBIAN_FRONTEND=noninteractive apt-get install -y docker.io docker-compose gnupg2 pass'
  sh 'docker swarm init || true'
  sh 'docker login --username=godfryd --password=donotchange cloud.canister.io:5000'

end

task :run_swarm => :build_docker_deploy do
  sh 'docker stack deploy --with-registry-auth -c docker-compose-swarm-deploy.yaml kraken'
end

task :run_portainer do
  sh 'docker volume create portainer_data'
  sh 'docker run -d -p 8000:8000 -p 9000:9000 -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer'
end

task :deploy_lab do
  sh "./venv/bin/fab -e -H lab.kraken.ci upgrade --kk-ver #{kk_ver}"
end

task :github_release do
  sh "curl --netrc  --fail --location --data '{\"tag_name\": \"v#{kk_ver}\"}' -o github-release-#{kk_ver}.json  https://api.github.com/repos/kraken-ci/kraken/releases"
  file = File.read("github-release-#{kk_ver}.json")
  rel = JSON.parse(file)
  upload_url = rel['upload_url'].chomp('{?name,label}')
  sh "curl --netrc --header 'Content-Type:application/gzip' --data-binary @kraken-docker-compose-#{kk_ver}.yaml '#{upload_url}?name=kraken-docker-compose-#{kk_ver}.yaml'"
end

task :release_deploy do
  Rake::Task["build_all"].invoke
  Rake::Task["docker_release"].invoke
  Rake::Task["github_release"].invoke
#  Rake::Task["deploy_lab"].invoke
end
