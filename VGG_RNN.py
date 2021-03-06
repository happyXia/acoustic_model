import torch
import torch.nn as nn
from tensorboardX import SummaryWriter
import torch.nn.functional as F
from utils import *


class AcousticModel(nn.Module):
    """
    4 layers of convolution and 4 layers of lstm with 2 fully connected layers.
    """
    def __init__(self, vocab_size, input_dimension):
        super(AcousticModel, self).__init__()
        self.vocab_size = vocab_size
        self.input_dimension = input_dimension
        self.num_rnn_layers = 4

        conv1 = nn.Sequential()
        conv1.add_module('conv1_conv1', convolution(in_channels=1, filter_size=32, bias=False))
        conv1.add_module('conv1_norm1', normalization(num_features=32))
        conv1.add_module('conv1_relu1', nn.ReLU())
        conv1.add_module('conv1_dropout1', nn.Dropout(p=0.1))
        conv1.add_module('conv1_conv2', convolution(in_channels=32, filter_size=32))
        conv1.add_module('conv1_norm2', normalization(num_features=32))
        conv1.add_module('conv1_relu2', nn.ReLU())
        conv1.add_module('conv1_maxpool', maxpooling(2))
        conv1.add_module('conv1_dropout2', nn.Dropout(p=0.1))
        self.conv1 = conv1

        conv2 = nn.Sequential()
        conv2.add_module('conv2_conv1', convolution(in_channels=32, filter_size=64))
        conv2.add_module('conv2_norm1', normalization(num_features=64))
        conv2.add_module('conv2_relu1', nn.ReLU())
        conv2.add_module('conv2_dropout1', nn.Dropout(p=0.1))
        conv2.add_module('conv2_conv2', convolution(in_channels=64, filter_size=64))
        conv2.add_module('conv2_norm2', normalization(num_features=64))
        conv2.add_module('conv2_relu2', nn.ReLU())
        conv2.add_module('conv2_maxpool', maxpooling(2))
        conv2.add_module('conv2_dropout2', nn.Dropout(p=0.1))
        self.conv2 = conv2

        conv3 = nn.Sequential()
        conv3.add_module('conv3_conv1', convolution(in_channels=64, filter_size=128))
        conv3.add_module('conv3_relu1', nn.ReLU())
        conv3.add_module('conv3_dropout1', nn.Dropout(p=0.2))
        conv3.add_module('conv3_norm1', normalization(num_features=128))
        conv3.add_module('conv3_conv2', convolution(in_channels=128, filter_size=128))
        conv3.add_module('conv3_norm2', normalization(num_features=128))
        conv3.add_module('conv3_relu2', nn.ReLU())
        conv3.add_module('conv3_maxpool', maxpooling(2))
        conv3.add_module('conv3_dropout2', nn.Dropout(p=0.2))
        self.conv3 = conv3

        conv4 = nn.Sequential()
        conv4.add_module('conv4_conv1', convolution(in_channels=128, filter_size=128))
        conv4.add_module('conv4_norm1', normalization(num_features=128))
        conv4.add_module('conv4_relu1', nn.ReLU())
        conv4.add_module('conv4_dropout1', nn.Dropout(p=0.2))
        conv4.add_module('conv4_conv2', convolution(in_channels=128, filter_size=128))
        conv4.add_module('conv4_relu2', nn.ReLU())
        conv4.add_module('conv4_conv3', convolution(in_channels=128, filter_size=128))
        conv4.add_module('conv4_norm2', normalization(num_features=128))
        conv4.add_module('conv4_relu3', nn.ReLU())
        conv4.add_module('conv4_dropout2', nn.Dropout(p=0.2))
        self.conv4 = conv4  # no maxpooling

        self.fc_features = int(input_dimension / 8 * 128)  # due to three times of pooling 2**3 = 8
        self.fc1 = fclayer(in_features=self.fc_features, out_features=128)
        self.fc2 = fclayer(in_features=256, out_features=128)
        self.fc3 = fclayer(in_features=128, out_features=vocab_size)
        self.rnn = normalRNN(in_features=128, out_features=128, rnn_type=nn.GRU, num_layers=4)

    def forward(self, x):
        conv1 = self.conv1(x)
        conv2 = self.conv2(conv1)
        conv3 = self.conv3(conv2)
        conv4 = self.conv4(conv3)
        # shape : (batch_size, channels, windows, dimension) => (batch size, windows, channels, dimension)
        # remember that when you transpose your tensor it only changes your stride which means you should
        # make this tensor contiguous by adding .contiguous()
        conv4 = conv4.transpose(1, 2).contiguous()
        out = conv4.view(-1, conv4.shape[1], self.fc_features)
        # conv4 = self.dropout(conv4)
        # print(conv4.shape)

        out = self.fc1(out)
        out = F.relu(out)
        # out shape: (batch_size,200,128)
        # out, h = self.rnn1(out)  # h shape (2,batch_size,256)
        # out = self.rnn1_layerNorm(out)
        # out, h = self.rnn2(out)
        # out = self.rnn2_layerNorm(out)
        # out, h = self.rnn3(out)
        # out = self.rnn3_layerNorm(out)
        # print(out.shape)
        # out = self.dropout(out)
        out, _ = self.rnn(out)
        out = self.fc2(out)
        # out = F.relu(out)
        # print(out.shape)
        out = self.fc3(out)
        out = F.log_softmax(out, dim=-1)
        out = out.transpose(0, 1).contiguous()  # (input_length, batch_size, number_classes) for ctc loss
        return out

    def convert(self, input_lengths):
        return input_lengths//8 + 1


if __name__ == "__main__":
    model = AcousticModel(1000, 200)
    print(model)
    dummy_input = torch.randn(3, 1, 1600, 200)
    print(model(dummy_input))
    # if torch.cuda.is_available():
    #     model = model.cuda()
    # summary(model, (1, 1600, 200))